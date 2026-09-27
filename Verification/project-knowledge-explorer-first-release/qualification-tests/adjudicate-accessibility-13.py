"""Index every original finding against attributed actual geometry and visual evidence."""
from pathlib import Path
from html.parser import HTMLParser
import json,hashlib,re,collections
ROOT=Path(__file__).resolve().parents[3];Q=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':sha(b),'bytes':len(b)}
def save(p,obj):
 b=(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode();assert len(b)<=250000
 with p.open('xb') as f:f.write(b)
 return ref(p)
def raw(row):
 p=Path(row['path']);b=p.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'];return json.loads(b)
class Anchor(HTMLParser):
 def __init__(self,s):super().__init__();self.href=None;self.text='';self.feed(s)
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.href=dict(attrs)['href']
 def handle_data(self,d):self.text+=d

def contrast(c):
 assert c['text_shadow']=='none'
 for a in c['ancestors']:assert a['background_image']=='none' and a['opacity']=='1' and a['filter']=='none' and a['mix_blend_mode']=='normal'
 bg=next(a['background'] for a in c['ancestors'] if a['background']!='rgba(0, 0, 0, 0)')
 def rgb(s):
  m=re.fullmatch(r'rgb\((\d+), (\d+), (\d+)\)',s);assert m;return [int(v)/255 for v in m.groups()]
 def lum(s):return sum(weight*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for weight,v in zip((.2126,.7152,.0722),rgb(s)))
 fg_l,bg_l=lum(c['foreground']),lum(bg);ratio=(max(fg_l,bg_l)+.05)/(min(fg_l,bg_l)+.05)
 size=float(c['font_size'].removesuffix('px'));weight=int(c['font_weight']);required=3 if size>=24 or (size>=18.6666667 and weight>=700) else 4.5
 assert ratio>=required
 return {'foreground':c['foreground'],'resolved_opaque_background':bg,'ratio':ratio,'required_text_ratio':required,'font_size':c['font_size'],'font_weight':c['font_weight'],'ancestor_effects':'All actually observed opacity 1, no background image/filter, normal blend; nearest opaque background used.'}

scanner=json.loads((Q/'actual-accessibility-13/stdout.json').read_text());geometry=json.loads((Q/'actual-geometry-02/stdout.json').read_text());visual=json.loads((Q/'actual-visual-03/stdout.json').read_text());original={(s['name'],s['theme']):s for s in scanner['scans']}
folder=Q/'accessibility-adjudication-13-02';folder.mkdir();states=[];counts=collections.Counter();zero=[];transient=[]
for gs in geometry['scans']:
 key=(gs['name'],gs['theme']);old=original[key];axe=raw(old['raw_report']);gm=raw(gs['raw_report']);mapped=[];incompletes=[]
 old_links=[c for c in old['targets_below24'] if c['tag']=='a'];new_links=[c for c in gm['candidates'] if c['tag']=='a']
 rule=next((r for r in axe['passes'] if r['id']=='target-size'),{})
 link_nodes=[n for n in rule.get('nodes',[]) if n['html'].startswith('<a ') and not any(c['id']=='target-size' for c in n['any'])]
 assert len(old_links)==len(new_links)==len(link_nodes)
 for o,n,a in zip(old_links,new_links,link_nodes):
  parsed=Anchor(a['html']);m=n['measurement'];assert m['center_hit_belongs_to_target'];assert all(not x['circle_intersects_target'] and not x['circles_intersect'] for x in m['neighbor_observations'])
  if key[0]!='overview':
   old_ord=int(re.search(r'li:nth-child\((\d+)\)',a['target'][0]).group(1));new_ord=int(re.search(r'li:nth-of-type\((\d+)\)',n['selector']).group(1));assert old_ord==new_ord
  same=parsed.text.strip()[:160]==n['text_preview'];timing=None
  if not same:
   assert key==('processes_index','light') and 'li:nth-child(2)' in a['target'][0] and parsed.text=='Fixture unordered inspection' and n['text_preview']=='Read this process'
   assert m['rect']['width']==o['width']==247.203125 and n['rect']['width']==152.53125
   timing='Initial collection saw pending label. Screenshot13 visibly shows recorded Fixture unordered inspection; later measurement width247.203125 equals original scanner label width. Immutable processes.ts13-24 retains row/link/href and changes textContent only. These observations were sequential, not atomic.';transient.append({'state':key[0],'theme':key[1],'selector':n['selector'],'qualification':timing})
  counts['standalone_anchor_spacing']+=1
  mapped.append({'original_candidate':o,'original_axe_selector':a['target'],'original_observed_href':parsed.href,'original_observed_text':parsed.text,'geometry_selector':n['selector'],'geometry_initial_text':n['text_preview'],'geometry_measured_rect':m['rect'],'center_hit':True,'nearby_target_count':len(m['neighbor_observations']),'any_24px_circle_intersection':False,'disposition':'Measured spacing exception supported; no inline-sentence exception asserted.','binding':'Exact state/theme, recorded anchor selector and ordered list position, same immutable row construction and text. Href is observed in original axe report only, not newly captured by geometry.','sequential_label_qualification':timing})
 old_inputs=[c for c in old['targets_below24'] if c['tag']=='input'];new_inputs=[t for t in gm['targets'] if t['input_type']=='checkbox']
 assert len(old_inputs)==len(new_inputs)
 for i,(o,n) in enumerate(zip(old_inputs,new_inputs)):
  assert o['width']==o['height']==19.1875
  field,label=(1,i+1) if i<3 else (2,i-2);suffix=f'fieldset:nth-of-type({field}) > label:nth-of-type({label}) > input:nth-of-type(1)';assert n['selector'].endswith(suffix)
  meaning=['draft','approved','deprecated','asserted','derived','inferred','external'][i]
  row={'original_candidate':o,'geometry_selector':n['selector'],'filter_value_from_immutable_construction':meaning,'geometry_initial_rect':n['rect'],'hidden_reasons':n['hidden_reasons'],'binding':'Same state/theme, complete seven-control set and exact two-fieldset/label order from unchanged search.ts55-56; cross-run numeric target indices are not equated.'}
  if n['hidden_reasons']:
   assert n['hidden_reasons']==['closed_details'];counts['closed_details_not_active']+=1;row['disposition']='Not an active pointer target while enclosing details is closed. Opened-filter controls separately observed.'
   if n['rect']['width']==0 or n['rect']['height']==0:
    assert i==0 and key[0] in ('relationship_list','display_limit_list');zero.append({'state':key[0],'theme':key[1],'original_candidate_index':o['index'],'geometry_selector':n['selector'],'value':'draft','observed_rect':n['rect'],'reason':'Retained full target row is closed-details zero rectangle; excluded solely by geometry below24 nonzero predicate.'})
  else:
   c=next(c for c in gm['candidates'] if c['selector']==n['selector']);m=c['measurement'];assert m['effective_target']=='associated_html_label' and m['label_control_association'];assert m['rect']['width']>=24 and m['rect']['height']>=24 and all(h['inside_viewport'] and h['belongs_to_target'] for h in m['sampled_24_square_hits']);counts['associated_label_size']+=1
   row.update(disposition='Associated actual HTML label supplies measured >=24px square hit area.',effective_rect=m['rect'],all_nine_square_hit_samples=True,actual_activation_qualification='All seven labels per theme have actual association and hit samples. Trusted click/change and restored filter request executed only on draft twice per theme, not on every distinct label.')
  mapped.append(row)
 assert len(mapped)==len(old['targets_below24'])
 arrows=iter([c for c in gm['colors'] if c['codepoints']==[8594]])
 for rule in axe['incomplete']:
  for node in rule['nodes']:
   check=next(c for k in ('any','all','none') for c in node[k] if c['id']=='color-contrast');kind=check['data']['messageKey'];selector=node['target'][0]
   if kind=='nonBmp':c=next(arrows);assert not c['hidden_reasons'];disposition='Actual U+2192 foreground/background chain exceeds text and nontext thresholds. Both-theme scrolled first-sentence images corroborate visible distinct arrows; repeated nodes retain their own measured chains.';counts['arrow_contrast']+=1
   else:
    assert kind=='bgOverlap'
    if selector=='#read-status > .warning':
     assert key==('combobox_suggestions','dark')
     other=original[('terms_browse','dark')];other_raw=raw(other['raw_report'])
     passed=next(n for r in other_raw['passes'] if r['id']=='color-contrast' for n in r['nodes'] if n['target']==node['target'])
     assert passed['html']==node['html']=='<p class="warning">source: The selected source is unavailable.</p>'
     check_data=next(c['data'] for c in passed['any'] if c['id']=='color-contrast')
     assert check_data['fgColor']=='#ffe3a3' and check_data['bgColor']=='#3f321b' and check_data['contrastRatio']==9.96
     counts['overlap_contrast']+=1
     incompletes.append({'rule':rule['id'],'original_selector':node['target'],'original_message_key':kind,'geometry_color_observation':None,'actual_unobscured_same_theme_report':other['raw_report'],'actual_unobscured_node_html':passed['html'],'actual_passed_check':check_data,'disposition':'Same exact warning selector and HTML directly pass in original same-theme unobscured Terms state at9.96:1. Geometry did not collect this warning color. Actual dark suggestions screenshot shows background warning partly covered by opened suggestions, with input focus visible. This is contrast review only; native focus remains unobserved.'})
     continue
    if selector=='#read-status > details > summary':c=next(c for c in gm['colors'] if c['text']=='Displayed knowledge version')
    elif selector=='.quiet':c=next(c for c in gm['colors'] if c['text']=='Refresh knowledge')
    elif selector=='#reading > h2':c=next(c for c in gm['colors'] if c['text']=='Terms')
    elif selector=='.scope':c=next(c for c in gm['colors'] if c['text']=='[scope text]')
    else:assert selector=='.model-summary > p:nth-child(1)';c=next(c for c in gm['colors'] if c['text'].startswith('5 terms and 7 relationships'))
    disposition='Actual foreground/background chain exceeds threshold. Suggestions overlay partially covers background reading content in observed image while search input remains visible; unobscured underlying states and explicit Escape flow are separately observed. At320px the scrolled summary/scope image visibly shows readable text without clipping. This settles contrast uncertainty only, not native keyboard focus or speech.';counts['overlap_contrast']+=1
   incompletes.append({'rule':rule['id'],'original_selector':node['target'],'original_message_key':kind,'geometry_selector':c['selector'],'codepoints':c['codepoints'],'geometry_rect':c['rect'],'computed_contrast':contrast(c),'disposition':disposition})
 assert next(arrows,None) is None
 value={'name':key[0],'theme':key[1],'original_raw_report':old['raw_report'],'geometry_raw_report':gs['raw_report'],'geometry_screenshot':gs['screenshot'],'target_candidate_mapping':mapped,'incomplete_node_mapping':incompletes,'limits':'Root executed browsers; worker performed attributed evidence arithmetic/source matching and viewed representative actual PNGs. No WCAG, native VoiceOver or complete focus-conformance claim.'}
 states.append(save(folder/(key[0]+'-'+key[1]+'.json'),value))
assert counts=={'standalone_anchor_spacing':150,'closed_details_not_active':140,'associated_label_size':14,'arrow_contrast':184,'overlap_contrast':8} and len(zero)==4 and len(transient)==1
result={'status':'all_original_192_incompletes_and_304_rectangle_candidates_individually_adjudicated_with_scoped_evidence','counts':dict(counts),'original_candidate_count':304,'geometry_candidate_count':300,'zero_rectangle_reconciliation':zero,'sequential_label_observation':transient,'state_evidence':states,'source_construction':[ref(ROOT/'SKILLS-depo/ontology/explorer/src/search.ts'),ref(ROOT/'SKILLS-depo/ontology/explorer/src/processes.ts'),ref(ROOT/'SKILLS-depo/ontology/explorer/src/map/list.ts')],'scanner_full_raw_index':ref(Q/'actual-accessibility-13/axe-complete-report-index.json'),'geometry_full_raw_index':ref(Q/'actual-geometry-02/geometry-complete-report-index.json'),'visual_full_raw_index':ref(Q/'actual-visual-03/visual-complete-report-index.json'),'actual_label_activation':geometry['label_activations'],'standards':['https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html','https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html'],'manual_visual_observation':{'observer':'/root/explorer_manager_g3/qualification_worker','actual_executor':'/root','six_visual03_images':'Independently viewed all six actual PNGs. Complete first sentence Alignment -> documents -> Alignment has two separate visible arrow glyphs in both themes. At320px object wraps to next line; recorded summary/scope/warnings and first sentence are readable without horizontal clipping in captured content.','geometry02_images_viewed':['02-filters_open-light','18-combobox_suggestions-dark','23-map_controls_320_css_pixels-dark','28-processes_index-dark','03-combobox_suggestions-light','13-processes_index-light','17-filters_open-dark','01-terms_browse-light'],'qualification':'Top viewport images alone did not show arrows or320px summary; visual03 specifically scrolled those regions. Visible search input focus outline is a screenshot observation, not native focus acceptance.'},'remaining_gates':['Actual Safari/VoiceOver on unlocked native desktop','Actual native zoom/reflow/focus/announcement observations and setting restoration','Windows/browser/assistive technology unexercised, explicitly recorded'],'no_blanket_conformance_claim':True}
print(json.dumps(save(Q/'accessibility-adjudication-13.json',result)))
