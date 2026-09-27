#!/usr/bin/env python3
"""Explicit local collaboration operations. No lifecycle writes or native invocation."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from collaboration_store import CollaborationError, encoded, read_json
from collaboration_task import Context
from collaboration_read import Board
from collaboration_delivery import pending
from collaboration_views import render, rebuild_view
from collaboration_decisions import assess, snapshot


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for option in ('project-root','task-path','assignment','actor','execution','policy-path','policy-sha256'):
        parser.add_argument('--'+option,required=True)
    parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('command',choices=['post','reply','list','read','search','digest','acknowledge','handle','delivery','pending','linked','validate','rebuild','snapshot','assess','proposal','overview','overview-rebuild'])
    parser.add_argument('--payload-file')
    for option in ('subtask','thread','participant','type','artifact','phase','search'):
        parser.add_argument('--'+option)
    parser.add_argument('--unread',action='store_true'); parser.add_argument('--offset',type=int,default=0); parser.add_argument('--items',type=int)
    args=parser.parse_args(argv)
    try:
        c=Context(args.project_root,args.task_path,args.assignment,args.actor,args.execution,args.generation,{'path':args.policy_path,'sha256':args.policy_sha256})
        board=Board(c)
        if args.payload_file and not (c.scope(args.payload_file) or c.scope(args.payload_file,'writes')):
            raise CollaborationError('COLLAB_SCOPE')
        supplied=read_json(c.root,args.payload_file) if args.payload_file else None
        filters={key:getattr(args,key) for key in ('subtask','thread','participant','type','artifact','phase','search','unread','offset','items')}
        if args.command in ('post','reply'): result=board.post(supplied)
        elif args.command in ('list','read','search','digest'): result=board.query(**filters)
        elif args.command in ('acknowledge','handle','delivery'):
            result=board.receipt(**supplied)
        elif args.command in ('overview','overview-rebuild'):
            from collaboration_overview import overview, rebuild_overview
            boards=[board]
            if supplied is not None:
                from collaboration_store import exact
                exact(supplied, ('boards',))
                if not isinstance(supplied['boards'],list) or len(supplied['boards'])>19: raise CollaborationError('COLLAB_BOUND')
                for binding in supplied['boards']:
                    exact(binding, ('task_path','assignment','execution','generation','policy'))
                    # Same actual actor in separately granted Tasks; no other identity impersonation.
                    boards.append(Board(Context(c.root,binding['task_path'],binding['assignment'],c.actor,binding['execution'],binding['generation'],binding['policy'])))
            operation=rebuild_overview if args.command=='overview-rebuild' else overview
            result=operation(boards,search=args.search,offset=args.offset,items=args.items or 20)
        elif args.command=='pending': result=pending(board,supplied['recipient'])
        elif args.command=='linked': result=board.linked(supplied['message_id'],supplied['reference'])
        elif args.command=='validate':
            visible=board.messages();receipts=board.receipts(visible)
            result={'valid':True,'visible_messages':len(visible),'visible_receipts':len(receipts),'task_mutated':False,'native_isolation_proved':False}
        elif args.command=='rebuild': result=rebuild_view(board,**filters)
        elif args.command=='snapshot': result=snapshot(board,**supplied)
        elif args.command=='assess': result=assess(board,**supplied)
        elif args.command=='proposal':
            from collaboration_proposals import proposal
            result=proposal(board,**supplied)
        output=encoded(result)
        # Read/delivery routes already paginate; other operations fail rather than leak.
        if len(output)>c.policy['bounds']['output_bytes']: raise CollaborationError('COLLAB_SIZE')
        print(output.decode()); return 0
    except (CollaborationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'error':getattr(exc,'code','COLLAB_INVALID')})); return 2


if __name__=='__main__':
    raise SystemExit(main())
