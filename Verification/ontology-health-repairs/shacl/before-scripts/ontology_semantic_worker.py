"""Trusted pinned FastEmbed worker. Reads local model files; rejects network and writes."""
import importlib.metadata
import json
import os
import sys

sys.dont_write_bytecode = True


def read_only(event, args):
    if event in {"socket.connect", "socket.bind", "subprocess.Popen", "os.system"}:
        raise PermissionError("Offline embedding workers cannot access the network or launch children.")
    if event == "open":
        mode = args[1]
        flags = args[2]
        if isinstance(mode, str) and any(c in mode for c in "wax+") or isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            raise PermissionError("Embedding reads cannot create or modify files.")
    if event in {"os.mkdir", "os.remove", "os.rename", "os.rmdir", "os.symlink", "os.link"}:
        raise PermissionError("Embedding reads cannot change persistent state.")


def main():
    if sys.version_info[:2] != (3, 12):
        raise ValueError("The selected semantic profile requires Python 3.12.")
    payload = json.loads(sys.stdin.read(20_000_001))
    packages = {name: importlib.metadata.version(name) for name in payload["packages"]}
    if packages != payload["packages"] or packages["fastembed"] != "0.8.0":
        raise ValueError("The installed runtime differs from the selected complete ontology package lock.")
    from fastembed import TextEmbedding
    from tokenizers import Tokenizer
    model_dir = payload["model_directory"]
    # FastEmbed's existing-directory mkdir(exist_ok=True) is performed once before
    # the audit guard; this exact directory is already verified by the caller.
    embedding = TextEmbedding(model_name=payload["model"], cache_dir=model_dir,
                              specific_model_path=model_dir, local_files_only=True,
                              threads=2, providers=["CPUExecutionProvider"], lazy_load=True)
    sys.addaudithook(read_only)
    tokenizer = Tokenizer.from_file(model_dir + "/tokenizer.json")
    tokenizer.no_truncation()
    counts = [len(tokenizer.encode(t).ids) for t in payload["texts"]]
    values = embedding.query_embed(payload["texts"]) if payload["query"] else embedding.embed(payload["texts"], batch_size=32)
    vectors = [v.tolist() for v in values]
    print(json.dumps({"status": "ok", "packages": packages, "python": sys.version.split()[0], "vectors": vectors,
                      "truncated_inputs": [i for i, count in enumerate(counts) if count > 512]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "failed", "diagnostic": type(error).__name__ + ": " + str(error)[:500]}))
        sys.exit(1)
