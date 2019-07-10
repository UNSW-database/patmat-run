# doExp find a sutiable machine to run exp.
# but note that when multiple process write to same file, the order can not be ensured.
# therefore, write all result into one line. as it is ensured that each line is either write into file or paused
import subprocess
import sys
import os
import time
import threading
import random
from subprocess import call


def extract(line, begin, end):
    res = line[line.find(begin) + len(begin):line.find(end)]
    # print(line, begin, end, res)
    return res


def execute(command):
    print(command)
    ssh = subprocess.Popen(command,
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    for _line in result:
        print(_line)


class TaskThread(threading.Thread):
    def __init__(self, _hostName, _command):
        threading.Thread.__init__(self)
        self.hostName = _hostName
        self.command = _command

    def run(self):
        # os.system(self.command)
        # subprocess.call(self.command, shell=True)
        ssh = subprocess.Popen(["ssh", "%s" % self.hostName, self.command],
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            error = ssh.stderr.readlines()
            print >> sys.stderr, "ERROR: %s" % error
        else:
            print(result)


class ExpThreadCreator:
    machines = list()
    sshFormatStr = "ssh -f xingfeng@%s.cse.unsw.edu.au "
    machineFilePath = "./machines"
    memLimit = 7 * (1024 ** 2)
    cpuLimit = 7.5
    sleepBetweenCpu = 0.2
    cpuCores = 8

    memBeginStr = "MemFree:"
    memEndStr = " kB"

    cpuSummaryBeginStr = "cpu  "

    @staticmethod
    def execute(command):
        print(command)
        return os.popen(command).read()

    @staticmethod
    def executeOnMachine(remotecommand, machine_name):
        sshcommand = ExpThreadCreator.sshFormatStr % (machine_name)
        return ExpThreadCreator.execute(sshcommand + "'" + remotecommand + "'")

    @staticmethod
    def isAvaiable(machine_name):
        sshcommand = ExpThreadCreator.sshFormatStr % (machine_name)
        remotecommand = "cat /proc/meminfo"
        results = ExpThreadCreator.execute(sshcommand + "'" + remotecommand + "'").split("\n")
        memResult = 0
        for line in results:
            # print("line", line, "memBeginStr", ExpThreadCreator.memBeginStr)
            if ExpThreadCreator.memBeginStr in line:
                memResult = int(line[
                                line.find(ExpThreadCreator.memBeginStr) + len(ExpThreadCreator.memBeginStr):line.find(
                                    ExpThreadCreator.memEndStr)])
        if memResult < ExpThreadCreator.memLimit:
            return False

        cpuRatio = 1
        remotecommand = "cat /proc/stat; sleep %f; cat /proc/stat" % (ExpThreadCreator.sleepBetweenCpu)
        results = ExpThreadCreator.execute(sshcommand + "'" + remotecommand + "'").split("\n")
        userTime = [0, 0]
        totalTime = [0, 0]
        timeIndex = 0
        for line in results:
            # print("line", line, "memBeginStr", ExpThreadCreator.memBeginStr)
            if ExpThreadCreator.cpuSummaryBeginStr in line:
                segments = line.split(" ")
                # print(segments)
                userTime[timeIndex] = int(segments[2]) + int(segments[4])
                totalTime[timeIndex] = userTime[timeIndex] + int(segments[5])
                timeIndex += 1

        if timeIndex == 2:
            cpuRatio = float(userTime[1] - userTime[0]) / (totalTime[1] - totalTime[0])

        print("Host %s Mem %dG cpu %.3f" % (machine_name, (memResult / (1024 ** 2)), cpuRatio))

        if (1 - cpuRatio) * ExpThreadCreator.cpuCores < ExpThreadCreator.cpuLimit:
            return False
        return True

    @staticmethod
    def check_status(machine_name):
        sshcommand = ExpThreadCreator.sshFormatStr % (machine_name)
        remotecommand = "cat /proc/meminfo"
        results = ExpThreadCreator.execute(sshcommand + "'" + remotecommand + "'").split("\n")
        memResult = 0
        for line in results:
            # print("line", line, "memBeginStr", ExpThreadCreator.memBeginStr)
            if ExpThreadCreator.memBeginStr in line:
                memResult = int(line[
                                line.find(ExpThreadCreator.memBeginStr) + len(ExpThreadCreator.memBeginStr):line.find(
                                    ExpThreadCreator.memEndStr)])

        cpuRatio = 1
        remotecommand = "cat /proc/stat; sleep %f; cat /proc/stat" % (ExpThreadCreator.sleepBetweenCpu)
        results = ExpThreadCreator.execute(sshcommand + "'" + remotecommand + "'").split("\n")
        userTime = [0, 0]
        totalTime = [0, 0]
        timeIndex = 0
        for line in results:
            # print("line", line, "memBeginStr", ExpThreadCreator.memBeginStr)
            if ExpThreadCreator.cpuSummaryBeginStr in line:
                segments = line.split(" ")
                # print(segments)
                userTime[timeIndex] = int(segments[2]) + int(segments[4])
                totalTime[timeIndex] = userTime[timeIndex] + int(segments[5])
                timeIndex += 1

        if timeIndex == 2:
            cpuRatio = float(userTime[1] - userTime[0]) / (totalTime[1] - totalTime[0])

        print("Host %s Mem %dG cpu %.3f" % (machine_name, (memResult / (1024 ** 2)), cpuRatio))

    @staticmethod
    def getTaskThread(command):
        while True:
            ExpThreadCreator.machines = list()
            machineFile = open(ExpThreadCreator.machineFilePath)
            for line in machineFile:
                if line == "\n":
                    continue
                ExpThreadCreator.machines.append(line.replace('\n', ''))
            # print(ExpThreadCreator.machines)
            machineFile.close()
            random.seed()
            randomHead = random.randint(0, len(ExpThreadCreator.machines))
            for i in range(len(ExpThreadCreator.machines)):
                machine = ExpThreadCreator.machines[(i + randomHead) % len(ExpThreadCreator.machines)]
                if (ExpThreadCreator.isAvaiable(machine)):
                    # create thread with command and return
                    sshcommand = ExpThreadCreator.sshFormatStr % (machine)
                    return TaskThread(machine, command)
            time.sleep(2)

    @staticmethod
    def getAvaMachine():
        while True:
            ExpThreadCreator.machines = list()
            machineFile = open(ExpThreadCreator.machineFilePath)
            for line in machineFile:
                if line == "\n":
                    continue
                ExpThreadCreator.machines.append(line.replace('\n', ''))
            # print(ExpThreadCreator.machines)
            machineFile.close()
            random.seed()
            randomHead = random.randint(0, len(ExpThreadCreator.machines))
            for i in range(len(ExpThreadCreator.machines)):
                machine = ExpThreadCreator.machines[(i + randomHead) % len(ExpThreadCreator.machines)]
                if (ExpThreadCreator.isAvaiable(machine)):
                    return machine
            time.sleep(2)


if __name__ == "__main__":
    resultThread = ExpThreadCreator.doExp("echo $HOSTNAME > ~/hostname.txt")
    resultThread.start()
