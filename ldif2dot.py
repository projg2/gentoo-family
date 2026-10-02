#!/usr/bin/env python

import argparse
import sys


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
            join, retire = (
                p.get(x, ['?']) for x in ('gentooJoin', 'gentooRetire')
            )
            label = '-'.join((join[0], retire[0]))
            if not retired:
                label = label.rstrip('?')

            attrs = []
            if retired:
                attrs.append('color="red"')
            name = f"{d}\\n({label})"
            print(f'  "{name}" [{", ".join(attrs)}];')
            dev_nodes.setdefault(d, {})[name] = (join, retire)

    # Output edges connecting rejoining developers.
    for dev_node, period_dict in dev_nodes.items():
        if len(period_dict) > 1:
            edges = ' -> '.join(f'"{x}"' for x in period_dict)
            print(f"  {edges} [style=dashed];")

    # Output edges connecting mentors to mentees.
    for mentor, mentees in relations.items():
        for mentee in mentees:
            # TODO: find the right node chronologically
            mentor_iter = iter(dev_nodes[mentor].items())
            mentee_iter = iter(dev_nodes[mentee].items())
            mentor_node, (mentor_join, mentor_retire) = next(mentor_iter)
            mentee_node, (mentee_join, mentee_retire) = next(mentee_iter)
            # mentee should be recruited while the mentor was a dev
            while True:
                try:
                    # if mentee joined earlier, look for a later rejoin
                    if mentor_join > mentee_join:
                        mentee_node, (mentee_join, mentee_retire) = next(mentee_iter)
                    # if mentee joined after mentor retired, see if they returned first
                    elif mentee_join > mentor_retire:
                        mentor_node, (mentor_join, mentor_retire) = next(mentor_iter)
                    else:
                        break
                except StopIteration:
                    print(f"Unable to match {mentor} -> {mentee}",
                          file=sys.stderr)
                    break
            print(f'  "{mentor_node}" -> "{mentee_node}";')

    print('}')


if __name__ == '__main__':
    main()
