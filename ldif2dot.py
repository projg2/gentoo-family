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
    relations = {}

    # Parse LDIF and collect mentor->dev relations.
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
                    relations.setdefault(m, []).append(uid)
                    devs.add(m)
                    devs.add(uid)

    # Split all collected developers (mentors and mentees) into periods.
    # Output all developer nodes.
    dev_nodes = {}
    for d in devs:
        devinfo = devinfos[d]
        retired = devinfo['gentooStatus'] == 'retired'
        years = sorted(
            (dt.split('/'), tp)
            for tp in ('gentooJoin', 'gentooRetire')
            for dt in devinfo.get(tp, []))

        periods = []
        prev = {}
        for yr, tp in years:
            if tp in prev:
                periods.append(prev)
                prev = {}
            prev[tp] = yr
        if prev:
            periods.append(prev)

        if not periods:
            periods = [{}]
        name = None
        for p in periods:
            label = '-'.join([p.get(x, ['?'])[0] for x
                                    in ('gentooJoin', 'gentooRetire')])
            if not retired:
                label = label.rstrip('?')

            attrs = []
            if retired:
                attrs.append('color="red"')
            name = f"{d}\\n({label})"
            print(f'  "{name}" [{", ".join(attrs)}];')
            dev_nodes.setdefault(d, {})[name] = p

    # Output edges connecting rejoining developers.
    for dev_node, period_dict in dev_nodes.items():
        if len(period_dict) > 1:
            edges = ' -> '.join(f'"{x}"' for x in period_dict)
            print(f"  {edges} [style=dashed];")

    # Output edges connecting mentors to mentees.
    for mentor, mentees in relations.items():
        # TODO: find the right node chronologically
        mentor_node = next(iter(dev_nodes[mentor]))
        for mentee in mentees:
            mentee_node = next(iter(dev_nodes[mentee]))
            print(f'  "{mentor_node}" -> "{mentee_node}";')

    print('}')


if __name__ == '__main__':
    main()
