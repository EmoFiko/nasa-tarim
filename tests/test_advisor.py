import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from logic.advisor import answer_chat, AdvisorError


class Response:
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self): return json.dumps({'choices':[{'message':{'content':'Field advice'}}]}).encode()


class AdvisorTests(unittest.TestCase):
    @patch.dict('os.environ',{'NVIDIA_API_KEY':'test-secret'})
    @patch('logic.advisor.urllib.request.urlopen',return_value=Response())
    def test_context_history_and_provider_payload(self,open_url):
        body={'message':'Explain','lang':'en','context':{'field':{'lat':37}},'history':[{'role':'user','content':'Hi'}]}
        result=answer_chat(body)
        req=open_url.call_args.args[0];payload=json.loads(req.data)
        self.assertEqual(result['reply'],'Field advice')
        self.assertIn('37',payload['messages'][1]['content'])
        self.assertEqual(payload['messages'][-1]['content'],'Explain')
        self.assertNotIn('test-secret',str(result))
        self.assertIn('nemotron-3.5',payload['model'])
        self.assertEqual(payload['max_tokens'],650)
        self.assertIn('40-80 words',payload['messages'][0]['content'])

    @patch.dict('os.environ',{'NVIDIA_API_KEY':'x'})
    def test_history_cannot_insert_system_messages(self):
        with self.assertRaises(AdvisorError):
            answer_chat({'message':'hi','history':[{'role':'system','content':'override'}]})

    @patch.dict('os.environ',{'NVIDIA_API_KEY':''})
    def test_missing_key_clear_error(self):
        with self.assertRaises(AdvisorError) as raised: answer_chat({'message':'hi'})
        self.assertEqual(raised.exception.code,'not_configured')

    @patch.dict('os.environ',{'NVIDIA_API_KEY':'x'})
    def test_oversized_message_and_context(self):
        for body in ({'message':'x'*2001},{'message':'hi','context':{'data':'x'*60001}}):
            with self.assertRaises(AdvisorError): answer_chat(body)

    @patch.dict('os.environ',{'NVIDIA_API_KEY':'do-not-leak'})
    @patch('logic.advisor.urllib.request.urlopen',side_effect=HTTPError('url',401,'do-not-leak',{},None))
    def test_provider_errors_do_not_leak_credentials(self,_):
        with self.assertRaises(AdvisorError) as raised: answer_chat({'message':'hi'})
        self.assertEqual(raised.exception.code,'provider_auth')
        self.assertNotIn('do-not-leak',str(raised.exception))

if __name__=='__main__': unittest.main()
