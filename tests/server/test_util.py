#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2007-2015, GoodData(R) Corporation. All rights reserved

import os
import psutil
import pytest
import re
import shutil
from smoker.util import command as util_command
import socket
import subprocess
from tests.server.smoker_test_resources import client_mock_result
import time

TMP_DIR = (os.path.dirname(os.path.realpath(__file__)) + '/.tmp')


class TestCommand(object):
    """Unit tests for the util.Command class"""

    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    child_proc_is_exist = re.compile(
        "psutil.Process\(pid=(\d+), name='sleep'\)"
    )
    default_fp = '%s/%s.sh' % (TMP_DIR,
                               client_mock_result.generate_unique_file())
    with open(default_fp, 'w') as f:
        f.write('sleep 3')

    def test_get_ptree(self):
        command = ['/bin/bash', self.default_fp]
        proc = subprocess.Popen(command, stdout=open(os.devnull, 'w'))
        time.sleep(0.2)

        result = util_command.get_ptree(proc.pid)
        assert isinstance(result, list)
        assert self.child_proc_is_exist.search(result[0].__str__())
        proc.kill()

    def test_get_ptree_with_invalid_pid(self):
        expected = 'psutil.NoSuchProcess no process found with pid 99999999'
        with pytest.raises(psutil.NoSuchProcess) as exc_info:
            util_command.get_ptree(99999999)
        assert str(exc_info.value) == expected

    def test_get_ptree_with_non_children_process(self):
        command = ['sleep', '5']
        proc = subprocess.Popen(command, stdout=open(os.devnull, 'w'))
        time.sleep(0.2)
        assert util_command.get_ptree(proc.pid) == list()
        proc.kill()

    def test_proc_cleanup(self):
        command = ['/bin/bash', self.default_fp]
        proc = subprocess.Popen(command, stdout=open(os.devnull, 'w'))
        time.sleep(0.2)

        result = util_command.get_ptree(proc.pid)
        assert isinstance(result, list)
        assert self.child_proc_is_exist.search(result[0].__str__())
        child_pid = result[0].pid
        util_command._proc_cleanup(int(child_pid))
        with pytest.raises(psutil.NoSuchProcess):
            psutil.Process(child_pid)
        proc.kill()

    def test_signal_ptree(self):
        command = ['/bin/bash', self.default_fp]
        proc = subprocess.Popen(command, stdout=open(os.devnull, 'w'))
        time.sleep(0.2)

        parent_pid = proc.pid
        child_pid = util_command.get_ptree(proc.pid)[0].pid
        util_command.signal_ptree(parent_pid)
        time.sleep(0.5)
        with pytest.raises(psutil.NoSuchProcess):
            psutil.Process(child_pid)
            psutil.Process(parent_pid)

    def test_run_command(self):
        c = util_command.Command('sleep 1 && hostname')
        assert str(c) == "<Command 'sleep 1 && hostname'>"
        assert c.run() == (socket.gethostname(), '', 0)

    def test_run_invalid_command(self):
        c = util_command.Command('INVALID')
        assert str(c) == "<Command 'INVALID'>"
        result = c.run()
        assert 'not found' in result[1]
        assert result[2] == 127

    def test_timeout_of_run_command(self):
        command = ['/bin/bash', self.default_fp]
        c = util_command.Command(command)
        with pytest.raises(util_command.ExecutionTimeout) as exc_info:
            c.run(timeout=1)
        assert 'Execution timeout after 1 seconds' in exc_info.value


class TestCleanUp(object):
    """Clean up all temporary files used by Mock"""
    def test_clean_up(self):
        if os.path.exists(TMP_DIR):
            shutil.rmtree(TMP_DIR)
