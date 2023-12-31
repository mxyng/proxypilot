import os
import json
from argparse import ArgumentParser
from aiohttp import web, ClientSession

import logging

logging.basicConfig(
  level=logging.DEBUG,
  format='%(asctime)s - %(levelname)s - [%(lineno)s] - %(message)s',
)


class OllamaRunner(web.View):

  base = os.getenv('OLLAMA_BASE', 'http://127.0.0.1:11434')

  async def _ollama_request(self):
    r = await self.request.json()

    language = r.get('extra', {}).get('language')
    model = {
      'python': os.getenv('OLLAMA_PYTHON_MODEL', 'codellama:7b-python'),
    }.get(language, os.getenv('OLLAMA_PYTHON_MODEL', 'codellama:7b-code'))

    return {
      'model': model,
      'template': '{{ .Prompt }}',
      'prompt': f'<PRE> {r.get("prompt")} <SUF>{r.get("suffix")} <MID>',
      'options': {
        'temperature': r.get('temperature'),
        'top_p': r.get('top_p'),
        'num_predict': r.get('max_tokens'),
        'stop': r.get('stop'),
      },
    }

  async def _generate(self):
    async with ClientSession(self.base) as s:
      async with s.post(
          '/api/generate',
          json=await self._ollama_request(),
      ) as r:
        r.raise_for_status()
        async for line in r.content:
          yield json.loads(line)

  def _openai_response(self, r):
    return json.dumps({
      'id': r.get('id'),
      'model': r.get('model'),
      'created': r.get('created'),
      'choices': [
        {
          'index': 0,
          'text': r.get('response'),
        },
      ],
    }).encode('utf-8')

  async def post(self):
    s = web.StreamResponse(headers={'Content-Type': 'text/event-stream'})
    await s.prepare(self.request)

    async for line in self._generate():
      if error := line.get('error'):
        raise Exception(error)

      await s.write(b'data: ')
      await s.write(self._openai_response(line))
      await s.write(b'\n')

    await s.write(b'[DONE]')
    return s


def main():
  parser = ArgumentParser()
  subparsers = parser.add_subparsers(required=True)

  ollama_parser = subparsers.add_parser('ollama')
  ollama_parser.set_defaults(runner=OllamaRunner)

  args = parser.parse_args()

  app = web.Application()
  app.router.add_route('*', '/{tail:.*}', args.runner)
  web.run_app(app, host='0.0.0.0', port=61107)


if __name__ == '__main__':
  main()
