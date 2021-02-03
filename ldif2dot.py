#!/usr/bin/env python

import argparse


MULTIVALUED_FIELDS = ['gentooJoin', 'gentooRetire', 'gentooMentor', 'uid']


def main():
    argp = argparse.ArgumentParser()
    argp.add_argument('input',
                      type=argparse.FileType('r'),
                      help='LDIF data to read')
    args = argp.parse_args()

    print('digraph "gentoo-family" {')
    print('  rankdir=LR;');

    devinfos = {}
    devs = set()

    for block in args.input.read().split('\n\n'):
        if not block:
            continue
        data = {}
        for l in block.split('\n'):
            k, v = l.split(': ', 1)
            if k in MULTIVALUED_FIELDS:
                data.setdefault(k, []).append(v)
            elif k in data:
                raise ValueError(f'Unexpected second value: {l} (uid={data["uid"]})')
            else:
                data[k] = v

        if len(data.get('uid', [])) != 1:
            continue
        uid = data['uid'][0]
        devinfos[uid] = data
        for ml in data.get('gentooMentor', []):
            for m in ml.split(','):
                m = m.strip()
                if m:
                    print(f'  "{m}" -> "{uid}";')
                    devs.add(m)
                    devs.add(uid)

    for d in devs:
        years = sorted(
            (dt.split('/'), tp)
            for tp in ('gentooJoin', 'gentooRetire')
            for dt in devinfos[d].get(tp, []))

        periods = []
        prev = {}
        for yr, tp in years:
            if tp in prev:
                periods.append(prev)
                prev = {}
            prev[tp] = yr
        if prev:
            periods.append(prev)

        labels = []
        for p in periods:
            labels.append('-'.join([p.get(x, ['?'])[0] for x
                                    in ('gentooJoin', 'gentooRetire')]))

        retired = devinfos[d]['gentooStatus'] == 'retired'
        attrs = []
        if labels:
            if not retired:
                labels[-1] = labels[-1].rstrip('?')
            attrs.append(f'label="\\N\\n({", ".join(labels)})"')
        if retired:
            attrs.append('color="red"')
        if attrs:
            print(f'  "{d}" [{", ".join(attrs)}];')

    print('}')


if __name__ == '__main__':
    main()
