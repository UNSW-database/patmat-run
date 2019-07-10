#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 15 17:11:43 2018

@author: zhengyi
"""


def get_machine_list(filepath):
    with open(filepath) as f:
        return [_line.strip().split(':')[0] for _line in f.readlines() if _line != '']


def sync_process(pool):
    for p in pool:
        p.wait()
    del pool[:]
