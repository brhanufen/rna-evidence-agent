"""Render saved computed reports and assemble a narrated decision walkthrough.

Not a screen capture, fresh model execution or reliability benchmark.
"""
from pathlib import Path
import json,re,subprocess,textwrap,wave,math
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/nightshift-demo-teaching';OUT.mkdir(parents=True,exist_ok=True)
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
im,d=base('Nightshift explains the computed checks','RECORDED NIGHTSHIFT RESPONSE / LOCAL QWEN 2.5 3B')
record=json.loads((ROOT/'output_examples/nightshift_design_01.json').read_text())
line(d,record['explanation'],175,size=26)
line(d,'Receipt: '+record['provider_receipt']['receipt_id'],505,'#64d4be',26)
line(d,'Computed decision: '+record['authoritative_decision'],552,'#ffd28a',25)
line(d,'Model prose cannot authorize analysis. Saved response, not a fresh live run.',647,'#b8cad7',21)
agent=OUT/'recorded-nightshift-explanation.png';im.save(agent)
scenes=[
(ROOT/'deliverables/revised-pitch/slide-1.png','Imagine you are about to compare two groups of RNA samples. Before choosing a statistical method, you need to understand how the samples are related.\n\nThis example follows one question: should these samples be paired? We will look at the evidence, and then see what happens when the input changes.'),
(agent,'Here is the explanation from Nightshift, using a local Qwen model. It says that matching identifiers aligns the files, but does not prove biological pairing.\n\nThe response and provider receipt are saved with the data fingerprint. The computed checks remain authoritative. The model cannot approve the design or start differential expression.'),
(paired,'Now read this table. Each row is a cell line. The next two columns show how many control and treated samples belong to it.\n\nEvery row has one of each. That gives us four apparent pairs. The workflow also checks that all eight sample identifiers match the count matrix.'),
(trace,'Here is the decision, step by step. The sample identifiers match, so the first check passes. There is one sample from each condition per cell line, so the second check passes.\n\nThe third check needs a person. Do these labels really describe the same experimental unit? Until that is confirmed, the workflow does not run differential expression.'),
(blocked,'Next, we deliberately replace one sample identifier in the metadata. This is a controlled example of an input mistake.\n\nThe workflow now stops. It cannot match the samples exactly, and it does not guess a match from their row positions. The report tells the researcher why analysis cannot continue.'),
(ROOT/'deliverables/revised-pitch/slide-4.png','Not every input change is an error. If we reverse the row order, the sample identifiers still match. The workflow correctly keeps the same request for confirmation.\n\nIf we change a pairing label instead, the pairs become unbalanced. That calls for design review. These examples show the difference between a harmless change and a meaningful problem.'),
(ROOT/'deliverables/nightshift-pitch/slide-6.png','The new integration brings these pieces together. Zetaris supplies the checked data. Meterless H MEM stores pointers to earlier runs. Nightshift is the primary AI provider for the design explanation. The evidence records show what was computed.\n\nThe design checks explain when to stop or ask. Cursor contributed viewer improvements. The existing RNA agent is disclosed separately from this new work.'),
(ROOT/'deliverables/nightshift-pitch/slide-7.png','Sixteen software tests passed before these Nightshift additions. The earlier Codex examples retain their evidence. The full Nightshift code execution loop still fails, and is not claimed as working.\n\nThe practical contribution is a decision the researcher can inspect: what passed, what failed, and what still needs confirmation. Broader evaluation and stronger execution isolation remain next steps.')]
# One continuous PCM narration track prevents per-segment AAC delay from
# shifting the audio relative to the image changes. Every scene has a lead-in
# and a reading pause; image duration is derived from its exact sample count.
segments=[];timeline=[];audio_parts=[];total_frames=0
fps=30;sample_rate=22050;samples_per_frame=sample_rate//fps
lead_frames=12;tail_frames=54
for i,(pic,narration) in enumerate(scenes):
    stem=OUT/f'segment-{i+1:02d}';stem.with_suffix('.txt').write_text(narration)
    paragraph_audio=[]
    for j,paragraph in enumerate(narration.split('\n\n')):
        part=OUT/f'speech-{i+1:02d}-{j+1:02d}.wav'
        subprocess.run(['/usr/bin/say','-r','120','--file-format=WAVE','--data-format=LEI16','-o',str(part),paragraph],check=True,timeout=60)
        with wave.open(str(part),'rb') as f:
            if (f.getframerate(),f.getnchannels(),f.getsampwidth())!=(sample_rate,1,2):raise RuntimeError('Unexpected narration format')
            raw=f.readframes(f.getnframes())
        if len(raw)<sample_rate*2:raise RuntimeError('Empty narration')
        if paragraph_audio:paragraph_audio.append(b'\0'*(round(0.65*sample_rate)*2))
        paragraph_audio.append(raw)
    pcm=b''.join(paragraph_audio);speech_samples=len(pcm)//2
    speech_frames=math.ceil(speech_samples/samples_per_frame)
    frames=lead_frames+speech_frames+tail_frames
    padded=(b'\0'*(lead_frames*samples_per_frame*2)+pcm+
            b'\0'*((speech_frames*samples_per_frame-speech_samples+tail_frames*samples_per_frame)*2))
    audio_parts.append(padded)
    timeline.append({'scene':i+1,'image':pic.name,'starts_at_seconds':round(total_frames/fps,3),
        'speech_starts_at_seconds':round((total_frames+lead_frames)/fps,3),
        'speech_ends_at_seconds':round((total_frames+lead_frames)/fps+speech_samples/sample_rate,3),
        'changes_at_seconds':round((total_frames+frames)/fps,3),'reading_pause_seconds':1.8})
    total_frames+=frames
    video=stem.with_suffix('.mp4')
    subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-loop','1','-framerate',str(fps),'-i',str(pic),'-frames:v',str(frames),'-an','-c:v','libx264','-tune','stillimage','-pix_fmt','yuv420p',str(video)],check=True,timeout=90)
    segments.append(video)
total=total_frames/fps
if not 60<=total<=240:raise RuntimeError('Narration duration outside required range')
continuous=OUT/'continuous-narration.wav'
with wave.open(str(continuous),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(sample_rate)
    for part in audio_parts:f.writeframes(part)
concat=OUT/'concat.txt';concat.write_text(''.join("file '"+str(p)+"'\n" for p in segments))
visual=OUT/'visual-timeline.mp4'
subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(visual)],check=True,timeout=90)
final=OUT/'RNA_Evidence_Agent_Nightshift_Demo_Teaching.mp4'
subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-i',str(visual),'-i',str(continuous),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-t',str(total),'-movflags','+faststart',str(final)],check=True,timeout=90)
subprocess.run([FF,'-hide_banner','-loglevel','error','-i',str(final),'-f','null','-'],check=True,timeout=60)
(OUT/'provenance.json').write_text(json.dumps({'video':final.name,'seconds':round(total,3),'speech_rate_wpm':120,'timing':'Single continuous PCM track, frame-aligned image durations, 0.4-second lead-in, 0.65-second paragraph pauses and at least 1.8-second reading pause per scene','scene_timeline':timeline,'format':'Narrated playback of computed JSON report panels and slides, not a screen capture or fresh live run','voice':'macOS system speech synthesis','controlled_cases':'original, mismatched ID, reversed rows, unbalanced pairing','model_run':'Recorded nightshift_design_01; no model calls in deterministic controlled cases; full Nightshift code-execution loop remains unsupported','full_decode':'passed'},indent=2)+'\n')
print(final);print('Total seconds:',round(total,3))
