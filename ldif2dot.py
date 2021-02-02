#!/usr/bin/env python

import argparse


def main():
    argp = argparse.ArgumentParser()
    argp.add_argument('input',
                      type=argparse.FileType('r'),
                      help='LDIF data to read')
    args = argp.parse_args()

    print('digraph "gentoo-family" {')
    print('  rankdir=LR;');

    devstates = {}
    devs = set()

    for block in args.input.read().split('\n\n'):
        if not block:
            continue
        data = dict(l.split(': ', 1) for l in block.split('\n'))
        if 'uid' not in data:
            continue
        devstates[data['uid']] = data['gentooStatus']
        mentors = [m.strip() for m in data.get('gentooMentor', '').split(',')
                   if m]
        for m in mentors:
            print(f'  "{m}" -> "{data["uid"]}";')
            devs.add(m)
            devs.add(data['uid'])

    for d in devs:
        if devstates[d] == 'retired':
            print(f'  "{d}" [color="red"];')

    print('}')


if __name__ == '__main__':
    main()
