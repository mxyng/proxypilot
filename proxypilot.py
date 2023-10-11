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
  model = os.getenv('OLLAMA_MODEL', 'codellama:7b-code')

  async def _ollama_request(self):
    r = await self.request.json()
    return {
      'model': self.model,
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
      await s.write(b'data: ')
      await s.write(self._openai_response(line))
      await s.write(b'\n')

    await s.write(b'[DONE]')
    return s


class OpenAIRunner(web.View):

  base = os.getenv('OPENAI_BASE')

  async def _generate(self):
    if not self.base:
      self.base = f'{self.request.headers["X-Forwarded-Proto"]}://{self.request.headers["X-Forwarded-Host"]}'

    async with ClientSession(self.base, headers=self.request.headers) as s:
      async with s.post(self.request.path_qs, json=await self.request.json()) as r:
        async for line in r.content:
          yield line

  async def post(self):
    s = web.StreamResponse(headers={'Content-Type': 'text/event-stream'})
    await s.prepare(self.request)

    async for line in self._generate():
      await s.write(b'data: ')
      await s.write(line)
      await s.write(b'\n')

    await s.write(b'[DONE]')
    return s


def main():
  parser = ArgumentParser()
  subparsers = parser.add_subparsers(required=True)

  ollama_parser = subparsers.add_parser('ollama')
  ollama_parser.set_defaults(runner=OllamaRunner)

  openai_parser = subparsers.add_parser('openai')
  openai_parser.set_defaults(runner=OpenAIRunner)

  args = parser.parse_args()

  app = web.Application()
  app.router.add_route('*', '/{tail:.*}', args.runner)
  web.run_app(app, host='0.0.0.0', port=61107)


if __name__ == '__main__':
  main()
