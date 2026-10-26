"""CPU fixtures for project integrity. These are not model quality tests."""
import json,os,re,sys,tempfile,unittest,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from text_processing import split_narration
from model_catalog import validate_selection,get_model
STORE=tempfile.TemporaryDirectory(prefix='vizra-test-',dir=os.environ.get('VIZRA_TEST_DIR'))
os.environ['VIZRA_WORKBENCH_ROOT']=STORE.name
import workbench_core as core
import studio_actions as actions

class FakeEngine:
    epoch=0
    def generate(self,kind,text,description,language,temperature,folder,prefix,epoch,reference=None):
        path=core.version_path(folder,prefix)
        core.sf.write(path,core.np.sin(core.np.arange(4800)*2*core.np.pi*440/24000)*.1,24000)
        meta=dict(text=text,model=kind,duration_seconds=.2,inference_seconds=.01,peak_allocated_mib=0,language=language)
        core.save_json(path.with_suffix('.json'),meta);return str(path),meta
    def stop(self):self.epoch+=1

class Workflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        core.ENGINE=FakeEngine()
        cls.reference=core.OUT/'favorites'/'reference.wav'
        core.sf.write(cls.reference,core.np.ones(24000)*.01,24000)
        core.save_json(cls.reference.with_suffix('.json'),dict(text='测试参考',favorite_name='测试'))

    def test_newlines_and_english_words(self):
        self.assertEqual(split_narration('第一行。\r\n\r\n第二行。\r第三行。'),['第一行。','第二行。','第三行。'])
        text=('This wireless head tracking module controls the camera and the flight simulator. '*35).strip()
        chunks=split_narration(text,100)
        self.assertEqual(re.findall(r'\w+|[^\w\s]',text),re.findall(r'\w+|[^\w\s]',' '.join(chunks)))
        self.assertTrue(all(len(x)<=100 for x in chunks))
        chinese='这是一个无线头追模块，它能够控制云台。'*70
        self.assertEqual(''.join(split_narration(chinese)),chinese)

    def test_capabilities(self):
        with self.assertRaises(ValueError):validate_selection('chatter','Chinese','reference')
        with self.assertRaises(ValueError):validate_selection('kokoro','English','reference')
        self.assertEqual(validate_selection('kokoro','English','am_michael').voice_mode,'preset')
        self.assertEqual(get_model('design').voice_mode,'design')

    def test_versions_and_exports(self):
        args=[None,'流程验收','第一段。\n第二段。',str(self.reference),'Chinese',.9,.3,100,core.MODEL_CLONE,'']
        result=list(actions.run_workflow('生成全部',*args))
        project=result[0][0]['value'];_,data=core.read_project(project)
        first=data['segments'][0]['selected'];second=data['segments'][1]['selected']
        digest=hashlib.sha256(Path(second).read_bytes()).hexdigest()
        request=json.dumps(dict(index=1,token=core.segment_table_token(data,1),text='只修改这一段。'))
        updates=list(actions.handle_segment_row(project,request,str(self.reference),'Chinese',.9,core.MODEL_CLONE,''))
        self.assertIn('row-spinner',updates[0][4]);_,data=core.read_project(project)
        self.assertIn('需要重新拼接',actions.export_state(data))
        self.assertEqual(hashlib.sha256(Path(second).read_bytes()).hexdigest(),digest)
        event=json.dumps(dict(index=1,token=core.segment_table_token(data,1),version=first))
        actions.row_update(project,event);_,data=core.read_project(project)
        self.assertEqual(data['segments'][0]['text'],'第一段。')
        target=actions.merge_project(project,.3)[0]
        self.assertEqual(target,actions.merge_project(project,.5)[0])
        audio,sr=core.sf.read(target);self.assertEqual(sr,48000)
        self.assertEqual(core.sf.info(target).subtype,'PCM_24')
        self.assertAlmostEqual(len(audio)/sr,.9,places=2)
        actions.clear_final(project);self.assertFalse(Path(target).exists());self.assertTrue(Path(first).exists())

    def test_preset_project_restores(self):
        args=[None,'English preset','This is the first line.\nHere is the second.','am_michael','English',.9,.2,100,get_model('kokoro').label,'']
        result=list(actions.run_workflow('生成全部',*args));project=result[0][0]['value']
        _,data=core.read_project(project);self.assertEqual(data['reference'],'am_michael')
        core.open_long(project)
        with self.assertRaises(Exception):core.redo_segment(project,1,'A replacement.','am_michael','Chinese',.9,get_model('kokoro').label,'')

if __name__=='__main__':unittest.main()
