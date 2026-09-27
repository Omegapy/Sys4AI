"""Match each actual scanner16 finding to geometry04; no browser execution."""
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

O = Path(__file__).resolve().parent
ROOT = O.parents[3]
CHECK_ONLY = sys.argv[1:] == ['--check']
assert CHECK_ONLY or sys.argv[1:] == []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ref(p):
    data = p.read_bytes()
    return {'path': str(p.relative_to(ROOT)), 'sha256': sha(data), 'bytes': len(data)}


def raw(row):
    data = Path(row['path']).read_bytes()
    assert len(data) == row['bytes'] and sha(data) == row['sha256']
    return json.loads(data)


class Anchor(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.href, self.text = None, ''
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs)['href']

    def handle_data(self, text):
        self.text += text


def contrast(color):
    assert color['text_shadow'] == 'none'
    for a in color['ancestors']:
        assert a['background_image'] == 'none' and a['opacity'] == '1' and a['filter'] == 'none' and a['mix_blend_mode'] == 'normal'
    background = next(a['background'] for a in color['ancestors'] if a['background'] != 'rgba(0, 0, 0, 0)')

    def luminance(value):
        m = re.fullmatch(r'rgb\((\d+), (\d+), (\d+)\)', value)
        assert m
        channels = [int(n) / 255 for n in m.groups()]
        return sum(w * (n / 12.92 if n <= .04045 else ((n + .055) / 1.055) ** 2.4) for w, n in zip((.2126, .7152, .0722), channels))

    fg, bg = luminance(color['foreground']), luminance(background)
    ratio = (max(fg, bg) + .05) / (min(fg, bg) + .05)
    size, weight = float(color['font_size'].removesuffix('px')), int(color['font_weight'])
    required = 3 if size >= 24 or size >= 18.6666667 and weight >= 700 else 4.5
    assert ratio >= required
    return {'foreground': color['foreground'], 'opaque_background': background, 'ratio': ratio, 'required_text_ratio': required, 'font_size': color['font_size'], 'font_weight': color['font_weight'], 'method': 'Actually observed ancestor chain: opacity1, no image/filter/shadow, normal blend; nearest opaque background. Calculated text contrast, distinct from pixel review.'}


scanner = json.loads(Path('/private/tmp/explorer-task022-host-ezsz8iud/stdout.json').read_text())
geometry = json.loads((O / 'actual-geometry-04/stdout.json').read_text())
assert sha(Path('/private/tmp/explorer-task022-host-ezsz8iud/stdout.json').read_bytes()) == 'f0df16af8d3957a905a6bef8f933facf163611ed66438216b9f606d9d547a78f'
assert sha((O / 'actual-geometry-04/stdout.json').read_bytes()) == '63ac49c256fcb99df67b1c4728832a82b3da5d187823d2671a43f66e53cba2b4'
original = {(s['name'], s['theme']): s for s in scanner['scans']}
counts, zero, transient, state_results = Counter(), [], [], []
for gs in geometry['scans']:
    key = gs['name'], gs['theme']
    old = original[key]
    axe, gm = raw(old['raw_report']), raw(gs['raw_report'])
    mapped, incompletes = [], []
    old_links = [c for c in old['targets_below24'] if c['tag'] == 'a']
    new_links = [c for c in gm['candidates'] if c['tag'] == 'a']
    rule = next((r for r in axe['passes'] if r['id'] == 'target-size'), {})
    link_nodes = [n for n in rule.get('nodes', []) if n['html'].startswith('<a ') and not any(c['id'] == 'target-size' for c in n['any'])]
    assert len(old_links) == len(new_links) == len(link_nodes)
    for old_target, target, node in zip(old_links, new_links, link_nodes):
        anchor, measurement = Anchor(node['html']), target['measurement']
        assert measurement['effective_target'] == 'element' and measurement['center_hit_belongs_to_target']
        assert not target['hidden_reasons'] and not target['disabled']
        assert all(not n['circle_intersects_target'] and not n['circles_intersect'] for n in measurement['neighbor_observations'])
        if key[0] != 'overview':
            old_order = int(re.search(r'li:nth-child\((\d+)\)', node['target'][0]).group(1))
            new_order = int(re.search(r'li:nth-of-type\((\d+)\)', target['selector']).group(1))
            assert old_order == new_order
        timing = None
        if anchor.text.strip()[:160] != target['text_preview']:
            assert key == ('processes_index', 'light') and old_order == 2
            assert anchor.text == 'Read this process' and target['text_preview'] == 'Fixture unordered inspection'
            assert old_target['width'] == target['rect']['width'] == measurement['rect']['width'] == 247.203125
            timing = 'Original axe HTML captured Read this process before the label resolved; the later scanner rectangle and both geometry rectangles have resolved width247.203125. Immutable processes.ts retains link/row/href and changes text. These fields were not captured atomically; href is only directly observed in original axe HTML.'
            transient.append({'state': key[0], 'theme': key[1], 'selector': target['selector'], 'qualification': timing})
        counts['standalone_anchor_spacing'] += 1
        mapped.append({'original_candidate': old_target, 'original_axe_selector': node['target'], 'original_observed_href': anchor.href, 'original_observed_text': anchor.text, 'geometry_selector': target['selector'], 'geometry_initial_text': target['text_preview'], 'measured_rect': measurement['rect'], 'center_hit': True, 'nearby_targets': len(measurement['neighbor_observations']), 'any_circle_target_or_circle_circle_intersection': False, 'disposition': 'Observed size/spacing supports the24px-circle spacing exception; no inline-sentence exception assumed.', 'binding': 'Exact state/theme, anchor element kind, ordered structural list position and label; raw cross-run numeric target indices are not equated.', 'sequential_label_qualification': timing})
    old_inputs = [c for c in old['targets_below24'] if c['tag'] == 'input']
    inputs = [t for t in gm['targets'] if t['input_type'] == 'checkbox']
    assert len(old_inputs) == len(inputs)
    for i, (old_target, target) in enumerate(zip(old_inputs, inputs)):
        assert old_target['width'] == old_target['height'] == 19.1875
        field, label = (1, i + 1) if i < 3 else (2, i - 2)
        assert target['selector'].endswith(f'fieldset:nth-of-type({field}) > label:nth-of-type({label}) > input:nth-of-type(1)')
        row = {'original_candidate': old_target, 'geometry_selector': target['selector'], 'filter_value_from_immutable_construction': ['draft', 'approved', 'deprecated', 'asserted', 'derived', 'inferred', 'external'][i], 'geometry_rect': target['rect'], 'hidden_reasons': target['hidden_reasons'], 'binding': 'Same state/theme and complete seven-control set, exact fieldset/label order from unchanged search.ts; no raw numeric-index equivalence.'}
        if target['hidden_reasons']:
            assert target['hidden_reasons'] in [['closed_details'], ['outside_open_modal_dialog', 'closed_details']]
            if 'outside_open_modal_dialog' in target['hidden_reasons']:
                assert key[0] == 'narrow_navigation_open'
                row['modal_basis'] = 'Actual dialog:modal observation and successful current modal keyboard sequence; background is inactive. Opened modal targets separately scanned.'
            counts['inactive_closed_details'] += 1
            row['disposition'] = 'Rectangle-only background/closed-details control is not an active pointer target in this state; actual opened-filter labels are separately measured.'
            if target['rect']['width'] == 0 or target['rect']['height'] == 0:
                assert i == 0 and key[0] in ['relationship_list', 'narrow_details_closed', 'display_limit_list']
                zero.append({'state': key[0], 'theme': key[1], 'original_candidate': old_target, 'full_retained_geometry_target': target, 'reason': 'Full closed-details target row retained with0x0 rectangle; excluded only from geometry nonzero below24 candidate subset.'})
        else:
            candidate = next(x for x in gm['candidates'] if x['selector'] == target['selector'])
            m = candidate['measurement']
            assert m['effective_target'] == 'associated_html_label' and m['label_control_association']
            assert m['rect']['width'] >= 24 and m['rect']['height'] >= 24
            assert all(h['inside_viewport'] and h['belongs_to_target'] for h in m['sampled_24_square_hits'])
            counts['associated_label_size'] += 1
            row.update(disposition='Actual associated HTML label contains a measured24px square with nine positive hit samples.', effective_rect=m['rect'], actual_activation_scope='Trusted draft label click/change/restoration twice per theme only; the other six labels have measured association/hit evidence, not individually observed activation.')
        mapped.append(row)
    mapped.sort(key=lambda x: x['original_candidate']['index'])
    assert [x['original_candidate'] for x in mapped] == old['targets_below24']
    colors = [c for c in gm['colors'] if c['codepoints'] == [8594] and not c['hidden_reasons']]
    used_arrows = set()
    for rule in axe['incomplete']:
        for node in rule['nodes']:
            check = next(c for group in ('any', 'all', 'none') for c in node[group] if c['id'] == 'color-contrast')
            kind, selector = check['data']['messageKey'], node['target'][0]
            if kind == 'nonBmp':
                li, span_child = map(int, re.search(r'li:nth-child\((\d+)\).*span:nth-child\((\d+)\)', selector).groups())
                assert span_child in [2, 4] and node['html'] == '<span> → </span>'
                matches = [c for c in colors if re.search(r'li:nth-of-type\(' + str(li) + r'\).*span:nth-of-type\(' + str(span_child // 2) + r'\)$', c['selector'])]
                assert len(matches) == 1
                color = matches[0]
                assert color['selector'] not in used_arrows
                used_arrows.add(color['selector'])
                counts['arrow_contrast'] += 1
                disposition = 'Actual U+2192 CSS foreground/background chain exceeds the text threshold. Current visible glyph/sentence evidence is separately required; no old-bundle pixels substituted.'
            else:
                assert kind == 'bgOverlap'
                if selector == '#read-status > details > summary':
                    color = next(c for c in gm['colors'] if c['text'] == 'Displayed knowledge version')
                elif selector == '.quiet':
                    color = next(c for c in gm['colors'] if c['text'] == 'Refresh knowledge')
                elif selector == '#reading > h2':
                    color = next(c for c in gm['colors'] if c['text'] == 'Terms')
                elif selector == '.scope':
                    color = next(c for c in gm['colors'] if c['text'] == '[scope text]')
                else:
                    assert selector == '.model-summary > p:nth-child(1)'
                    color = next(c for c in gm['colors'] if c['text'].startswith('5 terms and 7 relationships'))
                counts['overlap_contrast'] += 1
                disposition = 'Measured CSS chain exceeds threshold. Actual suggestions images and targeted current scrolled320 summary views qualify overlay/visibility separately. Ratio0 in axe incomplete is uncertainty, not a measured contrast failure.'
            incompletes.append({'rule': rule['id'], 'original_selector': node['target'], 'original_message_key': kind, 'geometry_selector': color['selector'], 'codepoints': color['codepoints'], 'geometry_rect': color['rect'], 'computed_contrast': contrast(color), 'disposition': disposition})
    assert len(used_arrows) == len(colors)
    assert [x['original_selector'] for x in incompletes] == [n['target'] for rule in axe['incomplete'] for n in rule['nodes']]
    state_results.append({'name': key[0], 'theme': key[1], 'original_raw': old['raw_report'], 'geometry_raw': gs['raw_report'], 'geometry_screenshot': gs['screenshot'], 'target_candidate_mapping': mapped, 'incomplete_node_mapping': incompletes})
assert counts == {'standalone_anchor_spacing': 188, 'inactive_closed_details': 252, 'associated_label_size': 14, 'arrow_contrast': 328, 'overlap_contrast': 8}
assert len(zero) == 6 and len(transient) == 1 and sum(len(x['target_candidate_mapping']) for x in state_results) == 454
if CHECK_ONLY:
    print(json.dumps({'status': 'read_only_mapping_checks_passed', 'counts': dict(counts), 'scanner_candidates': 454, 'geometry_candidates': 448, 'exact_zero_rectangle_reconciliations': len(zero), 'sequential_label_qualifications': len(transient), 'states': len(state_results), 'visual_review_pending': True}))
else:
    visual = json.loads((O / 'actual-visual-04/stdout.json').read_text())
    assert sha((O / 'actual-visual-04/stdout.json').read_bytes()) == 'f67e4d56bdfcbe5aea9181ef74b1d2fd30e1b0a954ccde81e38c1c35df83573b'
    assert visual['status'] == 'passed' and len(visual['scans']) == 8
    visual_by = {(x['name'], x['theme']): x for x in visual['scans']}
    folder = O / 'accessibility-adjudication-16-04'
    assert not folder.exists()
    folder.mkdir()

    def save(path, obj):
        data = (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode()
        assert len(data) <= 250000
        with path.open('xb') as f:
            f.write(data)
        return ref(path)

    state_refs = []
    for state in state_results:
        theme = state['theme']
        for node in state['incomplete_node_mapping']:
            if node['original_message_key'] == 'nonBmp':
                name = 'map_320_first_sentence' if state['name'].startswith('narrow_') or '320' in state['name'] else 'list_first_sentence'
                observed = visual_by[name, theme]
                observation = raw(observed['raw_report'])
                assert all(e['codepoints'] == [8594] and e['entire_rect_in_viewport'] and e['center_hit'] for e in observation['elements'])
                assert all(contrast(e)['foreground'] == node['computed_contrast']['foreground'] and contrast(e)['opaque_background'] == node['computed_contrast']['opaque_background'] for e in observation['elements'])
                node.update(current_visual=observed, disposition='Actual U+2192 text contrast exceeds threshold in this exact measured chain. Current both-theme first-sentence pixels show two legible arrows and adjacent labels. Repeated nodes share these measured glyph/color properties; individual offscreen arrows were not each visually inspected. The axe nonBmp classifier does not mean this codepoint exceeds U+FFFF.')
            elif state['name'] == 'combobox_suggestions':
                unobscured = original['terms_browse', theme]
                original_raw = raw(original[state['name'], theme]['raw_report'])
                source_node = next(n for r in original_raw['incomplete'] for n in r['nodes'] if n['target'] == node['original_selector'])
                passed = next(n for r in raw(unobscured['raw_report'])['passes'] if r['id'] == 'color-contrast' for n in r['nodes'] if n['target'] == node['original_selector'])
                assert source_node['html'] == passed['html']
                node.update(unobscured_current_same_html_report=unobscured['raw_report'], unobscured_passed_check=next(c['data'] for c in passed['any'] if c['id'] == 'color-contrast'), disposition='Actual same-theme same-selector/exact-HTML contrast passes in the unobscured Terms state; measured CSS chain also exceeds threshold. Current suggestions PNG shows the opened popup partly covering background reading text while the focused search input remains visible. This resolves contrast uncertainty, not all native focus/overlay behavior.')
            else:
                observed = visual_by['map_320_summary', theme]
                observation = raw(observed['raw_report'])
                assert all(e['entire_rect_in_viewport'] and e['center_hit'] for e in observation['elements'])
                node.update(current_visual=observed, disposition='Actual CSS text contrast exceeds threshold. Current scrolled320 summary/scope pixels show readable wrapped text and bounded warnings, without observed overlap in that viewport. Whole-page layout and native focus remain separate.')
        state['limits'] = 'Current root browser execution; worker source/geometry arithmetic and attributed viewport review. No full WCAG, native speech or whole-page unobscured claim.'
        state_refs.append(save(folder / (state['name'] + '-' + theme + '.json'), state))
    source_views = [visual_by['source_320_parent_dismissed', theme] for theme in ['light', 'dark']]
    for view in source_views:
        observed = raw(view['raw_report'])
        assert observed['source_parent_state']['details_hidden'] and observed['source_parent_state']['drawer_visible']
        assert observed['source_parent_state']['path'] == 'SPECS.md'
        assert observed['source_parent_state']['locator'] == 'Recorded locator: section:Specification'
        assert observed['elements'][0]['entire_rect_in_viewport'] and observed['elements'][0]['center_hit']
    result = {
        'status': 'all336_original_incompletes_and454_candidates_individually_adjudicated_with_scoped_current_evidence',
        'build_id': 'c02987099e81beb795595984e64bb81fcf2e64f4adee04d4c9fa607c16e72d5a',
        'counts': dict(counts), 'original_candidates': 454, 'geometry_candidates': 448,
        'geometry_active': 202, 'geometry_inactive': 246,
        'zero_rectangle_reconciliation': zero, 'sequential_label_observation': transient,
        'state_evidence': state_refs,
        'scanner_raw_index': ref(O / 'actual-accessibility-16/raw-shard-index.json'),
        'scanner_stdout_index': ref(O / 'actual-accessibility-16/stdout-index.json'),
        'geometry_raw_index': ref(O / 'actual-geometry-04/raw-shard-index.json'),
        'visual_raw_index': ref(O / 'actual-visual-04/raw-shard-index.json'),
        'actual_label_activation': geometry['label_activations'],
        'current_source_views': source_views,
        'source_construction': [ref(ROOT / ('SKILLS-depo/ontology/explorer/src/' + name)) for name in ['search.ts', 'processes.ts', 'map/list.ts']],
        'manual_visual_observation': {
            'actual_executor': '/root', 'worker_observer': '/root/explorer_manager_g3/qualification_worker',
            'root_geometry_review': ref(O / 'actual-geometry-04/root-visual-observation.json'),
            'root_targeted_review': ref(O / 'actual-visual-04/root-visual-observation.json'),
            'worker_viewed': 'All8 current visual04 PNGs plus geometry04 light source-parent-dismissed, dark320 Map, both-theme suggestions and opened filters.',
            'observations': ['Both themes show Alignment → documents → Alignment as two distinct arrows; at320px the second Alignment wraps to the next line while the arrow/label text remains legible.', 'Both320 summary views show readable wrapped scope text and bounded/omitted-item warnings.', 'Both320 dismissed-parent source views show Close source, Source evidence, SPECS.md, section:Specification and the complete short fixture excerpt. Hidden parent status is bound to observed DOM, not inferred solely from an absent panel in an image.', 'Suggestions partly cover underlying reading headings/status content; the actual focused search input outline is visible. Opened-filter labels and controls are readable in both captured themes.'],
            'limits': 'Viewport pixels only; graph/content outside the viewport is not asserted visible. The header truncates the fixture name. Geometry/contrast calculations are not native focus or screen-reader observations.'
        },
        'standards': ['https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html', 'https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html', 'https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html'],
        'remaining_gates': ['Permitted actual Safari Theme/native continuation method', 'Actual VoiceOver utterances and focused native AT observations', 'Windows/browser/AT combination unexercised; explicit limitation', 'TASK023 controlled protected read window, TASK024 measurements and TASK025 actual participant under original dependencies'],
        'no_blanket_conformance_claim': True
    }
    print(json.dumps(save(O / 'accessibility-adjudication.json', result)))
