#!/usr/bin/python3.7

import argparse
import asyncio
from os import path, listdir

import aiofiles
from aiohttp import ClientSession, MultipartWriter, ClientConnectionError, ClientPayloadError, ClientResponseError, FormData


async def upload_file(url, username, password, file_path, responses):
    async with aiofiles.open(file_path, mode='rb') as f:
        file_contents = await f.read()

    mpw = MultipartWriter()
    part = mpw.append(file_contents)
    part.set_content_disposition('attachment', filename=path.basename(file_path))

    fd = FormData()
    fd.add_field('file', file_contents, filename=path.basename(file_path))
    fd.add_field('username', username)
    fd.add_field('password', password)

    async with ClientSession() as session:
        try:
            async with session.post(url, data=fd) as response:
                response = await response.read()
                response_str = response.decode('utf-8')
                responses[response_str] = responses.get(response_str, 0) + 1
        except ClientConnectionError:
            responses['CONNECTION_ERR'] = responses.get('CONNECTION_ERR', 0) + 1
        except ClientPayloadError:
            responses['PAYLOAD_ERR'] = responses.get('PAYLOAD_ERR', 0) + 1
        except ClientResponseError:
            responses['RESPONSE_ERR'] = responses.get('RESPONSE_ERR', 0) + 1


async def status_printer(requests, responses):
    while True:
        print("Uploaded: %d files, responses: %s" % (requests['i'], responses))
        await asyncio.sleep(1.0)


async def load_gen(url, username, password, rate, files_folder, n_uploads):
    files_list = [path.join(files_folder, fn) for fn in listdir(files_folder)]

    responses = {}
    requests = {'i': 0}
    asyncio.create_task(status_printer(requests, responses))
    while n_uploads == 0 or requests['i'] < n_uploads:
        file_path = files_list[requests['i'] % len(files_list)]
        upload_task = upload_file(url, username, password, file_path, responses)
        asyncio.create_task(upload_task)
        requests['i'] += 1
        await asyncio.sleep(1.0 / rate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate file uploading load',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('url', metavar='URL', type=str, default="http://localhost:8000/",
                        help='Base url to upload files to')
    parser.add_argument('username', metavar='username', type=str, default="username",
                        help='Username')
    parser.add_argument('password', metavar='password', type=str, default="password",
                        help='Password')
    parser.add_argument('rate', metavar='R', type=float, nargs='?', default=0.5,
                        help='Rate of uploads (per second)')
    parser.add_argument('files_folder', metavar='files_folder', nargs='?', type=str, default="./files",
                        help='files folder path')
    parser.add_argument('n_uploads', metavar='N', type=int, nargs='?', default=0,
                        help='Total number of uploads (0 means infinity)')
    args=parser.parse_args()

    print("url: %s, rate: %f, files_folder: %s, n_uploads: %d" %
          (args.url, args.rate, args.files_folder, args.n_uploads))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(load_gen(args.url, args.username, args.password, args.rate, args.files_folder, args.n_uploads))



# 1_00000
# 1_00001