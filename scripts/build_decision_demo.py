"""Render saved computed reports and assemble a narrated decision walkthrough.

Not a screen capture, fresh model execution or reliability benchmark.
"""
from pathlib import Path
import json,re,subprocess,textwrap,wave
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/revised-demo';OUT.mkdir(parents=True,exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
CASES=json.loads((ROOT/'output_examples/design_cases.json').read_text())['scenarios']
def font(n):return ImageFont.truetype(FONT,n)
def base(title,kind):
    im=Image.new('RGB',(1280,720),'#101c29');d=ImageDraw.Draw(im)
    d.text((60,34),kind,font=font(21),fill='#64d4be')
    d.text((60,93),title,font=font(38),fill='#e8eef5')
    return im,d
def line(d,v,y,color='#e8eef5',size=27):
    for part in textwrap.wrap(v,82 if size<=27 else 70):
        d.text((60,y),part,font=font(size),fill=color);y+=39
    return y
# Panels are directly generated from stored JSON reports, not invented UI screenshots.
im,d=base('Eight samples, four apparent pairs','COMPUTED REPORT / ORIGINAL PUBLIC SNAPSHOT')
y=172
for text,x in [('Cell line',60),('Control',560),('Treated',830)]:d.text((x,y),text,font=font(27),fill='#b8cad7')
for i,p in enumerate(CASES['original']['pairs']):
    y=235+i*66
    for value,x in [(p['cell_line'],60),(str(p['control_samples']),560),(str(p['treated_samples']),830)]:d.text((x,y),value,font=font(30),fill='#e8eef5')
line(d,'Source: design_review.json | Sample alignment: exact ID match',562,'#64d4be',25)
line(d,'Saved deterministic result, not a fresh live model run',646,'#b8cad7',22)
paired=OUT/'computed-pairs.png';im.save(paired)
im,d=base('PASS / PASS / ASK','COMPUTED DECISION TRACE / ORIGINAL SNAPSHOT')
y=178
for item in CASES['original']['decision_trace']:
    y=line(d,item['result'].upper()+': '+item['check'],y,'#ffd28a' if item['result']=='pending' else '#64d4be',28)+24
line(d,CASES['original']['question'],438,size=28)
line(d,'Candidate only: '+CASES['original']['candidate_design'],555,'#64d4be',29)
line(d,'No biological confirmation supplied. No differential expression fitted.',648,'#b8cad7',22)
trace=OUT/'computed-trace.png';im.save(trace)
im,d=base('One ID changed: stop before analysis','CONTROLLED NEGATIVE CASE / MODIFIED METADATA')
y=line(d,'Changed input: one GSM sample ID was deliberately replaced.',181)
y=line(d,'Observed status: '+CASES['mismatched_id']['status'],y+30,'#ffd28a',29)
y=line(d,CASES['mismatched_id']['reason'],y+30)
y=line(d,CASES['mismatched_id']['decision_trace'][0]['consequence'],y+30)
line(d,'This is a deterministic guard, not an autonomous-agent trial.',646,'#b8cad7',23)
blocked=OUT/'computed-block.png';im.save(blocked)
im,d=base('The original agent asked for clarification','EARLIER RECORDED MODEL-DRIVEN RUN / CODEX_LIVE_03')
answer=json.loads((ROOT/'runs/codex_live_03/transcript.json').read_text())['final_answer']
quote=answer.split('\n\n')[-1]
line(d,'Exact excerpt from final_answer:',180,'#b8cad7',24)
line(d,quote,244,size=29)
line(d,'New work makes that unresolved assumption an explicit preflight decision.',510,'#64d4be',27)
line(d,'Saved execution artifact. Not a new live response.',648,'#b8cad7',23)
agent=OUT/'recorded-agent-question.png';im.save(agent)
scenes=[
(ROOT/'deliverables/revised-pitch/slide-1.png','Before running differential expression, a researcher needs to know whether the samples should be paired. RNA Evidence Agent makes the supporting evidence and missing confirmation visible. This walkthrough shows saved outputs from real executions, followed by new deterministic design checks.'),
(agent,'In the earlier recorded model driven run, the agent found four apparent cell line pairs. It asked whether cell line was the biological pairing unit, and which contrast and method to use. That question is valuable, but a question in prose can be overlooked. The new integration makes the decision explicit.'),
(paired,'Here is the computed report from the checked Zetaris export. Each of the four named cell lines has one control and one treated sample. Eight metadata sample identifiers match the count matrix exactly. These counts are recomputed from the files. They support a candidate paired structure; they do not establish the biological meaning of the labels.'),
(trace,'The decision trace separates three checks. Sample alignment passes. One sample per condition within each cell line passes. Biological pairing remains pending. The report proposes a candidate design, then stops for researcher confirmation. No differential expression is fitted. A confirmation record must match the dataset fingerprint, factor and contrast.'),
(blocked,'Now change one metadata sample identifier deliberately. The observed result is blocked input alignment. The workflow stops before proposing or fitting an analysis, rather than joining samples by row position. This negative control shows the new deterministic guard working. It is not a claim about autonomous agent accuracy.'),
(ROOT/'deliverables/revised-pitch/slide-4.png','A useful check must also accept harmless changes. Reversing metadata row order still requests pairing confirmation, because identifiers still match. Changing a pairing label creates an imbalance and requests design review. These controlled cases make the difference between stop and ask behavior inspectable.'),
(ROOT/'deliverables/revised-pitch/slide-5.png','The hackathon adds Zetaris access and a checked snapshot, Meterless dataset specific run pointers, evidence references, and the explicit design gate. Cursor contributed viewer labeling and navigation. The existing RNA agent loop, prompts, executor and dataset are disclosed separately. This is integration work around that baseline.'),
(ROOT/'deliverables/revised-pitch/slide-6.png','Sixteen focused software tests pass. Three earlier model driven demonstrations contain thirty four linked output references. Neither is a general reliability score. The contribution is an inspectable record of what was checked and why the workflow stopped or asked. Independent benchmarking and stronger execution isolation remain next steps.')]
segments=[];total=0
for i,(pic,narration) in enumerate(scenes):
    stem=OUT/f'segment-{i+1:02d}';stem.with_suffix('.txt').write_text(narration)
    subprocess.run(['/usr/bin/say','-r','160','--file-format=WAVE','--data-format=LEI16','-o',str(stem.with_suffix('.wav')),'-f',str(stem.with_suffix('.txt'))],check=True,timeout=60)
    with wave.open(str(stem.with_suffix('.wav')),'rb') as f:seconds=f.getnframes()/f.getframerate()
    if seconds<1:raise RuntimeError('Empty narration')
    total+=seconds
    video=stem.with_suffix('.mp4')
    subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-loop','1','-framerate','10','-i',str(pic),'-i',str(stem.with_suffix('.wav')),'-t',str(seconds),'-c:v','libx264','-tune','stillimage','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(video)],check=True,timeout=90)
    segments.append(video)
if not 60<=total<=240:raise RuntimeError('Narration duration outside required range')
concat=OUT/'concat.txt';concat.write_text(''.join("file '"+str(p)+"'\n" for p in segments))
final=OUT/'RNA_Evidence_Agent_Decision_Demo.mp4'
subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)],check=True,timeout=90)
subprocess.run([FF,'-hide_banner','-loglevel','error','-i',str(final),'-f','null','-'],check=True,timeout=60)
(OUT/'provenance.json').write_text(json.dumps({'video':final.name,'seconds_narration':round(total,2),'format':'Narrated playback of computed JSON report panels and slides, not a screen capture or fresh live run','voice':'macOS system speech synthesis','controlled_cases':'original, mismatched ID, reversed rows, unbalanced pairing','model_run':'Earlier codex_live_03; no new model execution in controlled cases','full_decode':'passed'},indent=2)+'\n')
print(final);print('Narration seconds:',round(total,2))
