"""Assemble an explicitly recorded-artifact walkthrough; no screen capture claim."""
from pathlib import Path
import json
import wave
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables';MEDIA=OUT/'video-build';MEDIA.mkdir(parents=True,exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def scene(name,title,lines):
    im=Image.new('RGB',(1280,720),'#101c29');d=ImageDraw.Draw(im)
    d.text((64,40),'RECORDED EXECUTION ARTIFACTS',font=ImageFont.truetype(FONT,21),fill='#64d4be')
    d.text((64,100),title,font=ImageFont.truetype(FONT,39),fill='#e8eef5')
    y=195
    for line in lines:
        for part in textwrap.wrap(line,78):
            d.text((64,y),part,font=ImageFont.truetype(FONT,26),fill='#e8eef5');y+=39
        y+=17
    d.text((64,662),'Public GSE52778 data · selected demonstrations, not a benchmark',font=ImageFont.truetype(FONT,21),fill='#b8cad7')
    p=MEDIA/(name+'.png');im.save(p);return p
r1=json.loads((ROOT/'runs/codex_live_01/transcript.json').read_text())
r2=json.loads((ROOT/'runs/codex_live_02/transcript.json').read_text())
failures=[s for s in r2['steps'] if s.get('code') is not None and not s.get('ok')]
assert len(failures)==2
inv=scene('inventory','Computed inventory', ['21,833 gene rows; 8 samples','4 control and 4 treated samples','Unique sample identifiers match exactly','Source: codex_live_01/transcript.json; 13 registered references'])
recovery=scene('recovery','Errors remain in the execution record',['First attempt: matplotlib was unavailable','Second attempt: manual PNG font lookup raised KeyError','The agent corrected its code and produced a PNG','5 steps; 2 execution errors; 166.14 seconds','Source: codex_live_02/transcript.json'])
pair=scene('pairing','A method decision needs clarification',['4 cell lines, each with one control and one treated sample','The agent asked for pairing and contrast confirmation before differential expression','No clinical conclusion is established','Source: codex_live_03/transcript.json'])
scenes=[
(OUT/'pitch-renders/slide-1.png','RNA Evidence Agent is my solo hackathon project. It connects public RNA sequencing data to a code execution agent, while preserving the source, calculations, errors, and evidence references. This video walks through saved outputs from real executions. It is not a fresh live run.'),
(OUT/'pitch-renders/slide-3.png','Zetaris provides the count matrix and metadata through declared tables. The agent uses Codex to choose a calculation, executes Python, observes the output, and can correct an error. Meterless H MEM stores dataset specific run pointers. Cursor contributed the recorded viewer labeling and navigation.'),
(inv,'The first demonstration inventories the data exported through Zetaris. Python counted twenty one thousand eight hundred thirty three gene rows and eight samples, with four control and four treated samples. The sample identifiers matched exactly. Each registered claim points to an exact excerpt of successful output.'),
(recovery,'The depth quality control task encountered two execution errors. Matplotlib was unavailable, and a second attempt hit a font lookup error. The agent corrected the code and produced its figure. Both failures remain in the transcript. This demonstrates recovery in this one run, not a general recovery rate.'),
(OUT/'pitch-renders/slide-5.png','These bars show summed counts in the supplied matrix for each sample. They are not total sequenced reads. The matrix was filtered before the hackathon to retain genes with total counts of at least ten. Count depth alone cannot establish read quality or differential expression.'),
(pair,'The third run inspected the experimental design. It found four cell lines, each represented by a control and treated sample. Before differential expression, the agent asked for confirmation of the biological pairing and analysis contrast. This keeps an unresolved method choice visible.'),
(OUT/'pitch-renders/slide-4.png','Across the three selected runs, thirty four explicitly registered references matched successful Python output. That is an output traceability check. It does not prove every sentence is covered, the statistical method is correct, or the agent is reliable across unseen tasks. Eight focused software regression tests also passed.'),
(OUT/'pitch-renders/slide-6.png','The pre existing RNA agent is disclosed separately from the new integration. The offline sample works without model access. Live execution uses an authorized local model account. This prototype uses trusted public data; Python execution is not a security sandbox. Next steps are independent benchmarking, stronger isolation, and analyst review.')]
segments=[]
for i,(pic,narration) in enumerate(scenes):
    stem=MEDIA/f'scene-{i+1:02d}';stem.with_suffix('.txt').write_text(narration)
    subprocess.run(['/usr/bin/say','-r','155','--file-format=WAVE','--data-format=LEI16','-o',str(stem.with_suffix('.wav')),'-f',str(stem.with_suffix('.txt'))],check=True,timeout=60)
    with wave.open(str(stem.with_suffix('.wav')),'rb') as audio:
        duration=audio.getnframes()/audio.getframerate()
    if duration<1: raise RuntimeError('Speech synthesis returned empty audio; use authorized local speech service access')
    video=stem.with_suffix('.mp4')
    subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-loop','1','-framerate','10','-i',str(pic),'-i',str(stem.with_suffix('.wav')),'-t',str(duration),'-c:v','libx264','-tune','stillimage','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(video)],check=True,timeout=90)
    segments.append(video)
concat=MEDIA/'concat.txt';concat.write_text(''.join("file '"+str(p)+"'\n" for p in segments))
video=OUT/'RNA_Evidence_Agent_Recorded_Walkthrough.mp4'
subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(video)],check=True,timeout=90)
(OUT/'video-provenance.json').write_text(json.dumps({'format':'Narrated walkthrough of recorded artifacts, not screen capture or a fresh live run','voice':'macOS system speech synthesis','sources':['runs/codex_live_01','runs/codex_live_02','runs/codex_live_03','pitch-renders'],'path':video.name},indent=2)+'\n')
print(video)
