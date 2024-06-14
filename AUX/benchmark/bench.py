from src.convertImage import convertToHaskell
from src.color import Colors

import argparse
import os
import toml
import tomllib
import time

def validate_file(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"{path} is not a valid file.")
    return path


def convertTestFile(path, testDir, generate, verbose=False):
    fName = f"{testDir}/{path.split('/')[-1].split('.')[0]}".replace(" ", "_")
    if generate == "auto":
        if os.path.isfile(fName):
            if os.path.getmtime(fName) < os.path.getmtime(path):
                if verbose:
                    print(f"File {Colors.BOLD}[\"{fName}\"]{Colors.RESET} is older than {path} and will be updated")
                convertToHaskell(path, fName, verbose)
                return
            else:
                if verbose:
                    print(f"File {Colors.BOLD}{Colors.BOLD}[\"{fName}\"]{Colors.RESET}{Colors.RESET} is already up to date")
                return
        if verbose:
            print(f"File {Colors.BOLD}[\"{fName}\"]{Colors.RESET} does not exist, we will create it.")
        convertToHaskell(path, fName, verbose)
    else:
        if verbose:
            print(f"File {Colors.BOLD}[\"{fName}\"]{Colors.RESET} has been created.")
        convertToHaskell(path, fName, verbose)

def getAllFiles(path):
    if not os.path.exists(path):
        return []
    if os.path.isfile(path):
        return [path]
    entries = os.listdir(path)
    if not entries:
        return []
    return [f"{path}/{i}" for i in entries if os.path.isfile(f"{path}/{i}")]

parser = argparse.ArgumentParser(description='Process some files.')
parser.add_argument('-V', '--verbose', action='store_true', help='active Verbose mode')
parser.add_argument('-C', '--config', help='config file', type=validate_file, required=True)
parser.add_argument('--cli', action='store_true', help='active CLI interactive mode')

args = parser.parse_args()

try:
    with open(args.config, 'rb') as f:
        config = tomllib.load(f)
except:
    raise Exception("Bad config file")

if "config" not in config or "paths" not in config["config"] or not config["config"]["paths"]:
    raise Exception("Bad config file")

# Set Tmp file

tmpFile = "tmp"

if config["config"]["tmp_dir"]:
    tmpFile = config["config"]["tmp_dir"]

# Clear tmp file

if os.path.exists(tmpFile):
    if os.path.isfile(tmpFile):
        os.remove(tmpFile)
        os.makedirs(tmpFile)
else:
    os.makedirs(tmpFile)

# get allFiles to create haskell files

allFiles = set([i for i in [getAllFiles(j) for j in config["config"]["paths"] if os.path.exists(j)] if i != []][0])

# Set test Dir
testDir = "test"

if config["config"]["test_dir"]:
    testDir = config["config"]["test_dir"]

if os.path.exists(testDir):
    if os.path.isfile(testDir):
        os.remove(testDir)
        os.makedirs(testDir)
else:
    os.makedirs(testDir)

# Set generate option
generate = "auto"

if not config["config"]["generate"] or config["config"]["generate"] != "auto":
    generate = "force"

for i in allFiles:
    convertTestFile(i, testDir, generate, args.verbose)

allTestFiles = getAllFiles(testDir)

if not allTestFiles:
    raise Exception("No files to test")

# Set binary
binary = "imageCompressor"

if "bin" in config["config"] and config["config"]["bin"]:
    binary = config["config"]["bin"]

if not os.path.isfile(binary):
    raise Exception(f"Binary {binary} does not exist")

# Set Ref Binary
refBinary = "imageCompressor"

if "ref_bin" in config["config"] and config["config"]["ref_bin"]:
    refBinary = config["config"]["ref_bin"]

if not os.path.isfile(refBinary):
    raise Exception(f"Binary {refBinary} does not exist")

def getDistance(path) -> int:
    dist = 0
    with open(path, "r") as f:
        lines = f.readlines()
        while lines:
            line = lines.pop(0)
            if line == "--\n":
                line = lines.pop(0)
                cluster = list(map(int,line[1:-2].split(",")))
                continue
            if line == "" or line == "\n" or line == "-\n":
                continue
            r, g, b = map(int, line.split(") (")[1][:-2].split(","))
            dist += abs(r - cluster[0]) + abs(g - cluster[1])+ abs(b - cluster[2])
    return dist

def printResult(test, bin, ref, distBin, distRef, timeBin, timeRef):
    if bin != ref:
        print(f"\tTest {Colors.BOLD}{testDir}/{test}{Colors.RESET} {Colors.RED}FAILED{Colors.RESET}")
        return 0
    color = Colors.GREEN
    colorDist = Colors.GREEN
    colorTime = Colors.GREEN
    if distRef / distBin < 0.80:
        colorDist = Colors.RED
    elif distRef / distBin < 0.90:
        colorDist = Colors.YELLOW
    if timeRef / timeBin > 1.5:
        colorTime = Colors.RED
    elif timeRef / timeBin > 1.2:
        colorTime = Colors.YELLOW

    if colorDist == Colors.RED or colorTime == Colors.RED:
        color = Colors.RED
    elif colorDist == Colors.YELLOW or colorTime == Colors.YELLOW:
        color = Colors.YELLOW
    print(f"    Test {Colors.BOLD}{testDir}/{test}{Colors.RESET} {color}PASSED{Colors.RESET} ->\n        {colorDist}Dist Ratio: {distBin/distRef:.4f}%{Colors.RESET}\n        {colorTime}Time Ratio: {timeBin/timeRef:.4f}%{Colors.RESET}")
    return 1

def runTest(test, binary, refBinary, args, testDir, verbose=False):
    if verbose:
        print(f"Run test {test}")
        print(f"Run {binary} -n {args['-n']} -l {args['-l']} -f {testDir}/{test} > {tmpFile}/{test}.out")
    binStart = time.time()
    bin = os.system(f"{binary} -n {args['-n']} -l {args['-l']} -f {testDir}/{test} > {tmpFile}/{test}.out")
    binEnd = time.time()
    distBin = getDistance(f"{tmpFile}/{test}.out")

    if verbose:
        print(f"Run {refBinary} -n {args['-n']} -l {args['-l']} -f {testDir}/{test} > {tmpFile}/{test}.ref")
    refStart = time.time()
    ref = os.system(f"{refBinary} -n {args['-n']} -l {args['-l']} -f {testDir}/{test} > {tmpFile}/{test}.ref")
    refEnd = time.time()
    distRef = getDistance(f"{tmpFile}/{test}.ref")
    return (bin, ref, distBin, distRef, binEnd - binStart, refEnd - refStart)


# Process Tests

def runTests(i):
    if i == "config" or not "test_name" in config[i] or not "test_files" in config[i] or not config[i]["test_files"] or not "-n" in config[i] or not "-l" in config[i]:
        return 0
    average = 1
    if "average" in config[i] and config[i]["average"] > 1:
        average = config[i]["average"]
    if average > 1:
        print(f"{Colors.BOLD}Test [{Colors.MAGENTA}{config[i]['test_name']}{Colors.WHITE}]{Colors.RESET} {Colors.BOLD}[{Colors.CYAN}{average}{Colors.RESET}{Colors.BOLD} times]{Colors.RESET}")
    else:
        print(f"{Colors.BOLD}Test [{Colors.MAGENTA}{config[i]['test_name']}{Colors.WHITE}]{Colors.RESET} {Colors.BOLD}[{Colors.CYAN}OS{Colors.RESET}{Colors.BOLD}]")
    tmpPassed = 0
    tmpStatus = True
    for j in config[i]["test_files"]:
        bin, ref, distBin, distRef, binTime, refTime = (0, 0, 0, 0, 0, 0)
        for _ in range(average):
            binTmp, refTmp, distBinTmp, distRefTmp, binTimeTmp, refTimeTmp = runTest(j, binary, refBinary, {"-n": config[i]["-n"], "-l": config[i]["-l"]}, testDir, args.verbose)
            bin += binTmp
            ref += refTmp
            distBin += distBinTmp
            distRef += distRefTmp
            binTime += binTimeTmp
            refTime += refTimeTmp
        bin /= average
        ref /= average
        distBin /= average
        distRef /= average
        binTime /= average
        refTime /= average
        if printResult(j, bin, ref, distBin, distRef, binTime, refTime):
            tmpPassed += 1
        else:
            tmpStatus = False
            break
    if tmpStatus:
        print(f"Test {Colors.BOLD}{config[i]['test_name']}{Colors.RESET} {Colors.GREEN}PASSED{Colors.RESET} {tmpPassed}/{len(config[i]['test_files'])}\n")
    else:
        print(f"Test {Colors.BOLD}{config[i]['test_name']}{Colors.RESET} {Colors.RED}FAILED{Colors.RESET}\n")
    return tmpPassed

def processTests(*arg):
    test = 0
    passed = 0
    if arg:
        for i in arg:
            if i == "config" or not i in config:
                continue
            passed += runTests(i)
            test += len(config[i]['test_files'])
        print(f"Test {Colors.BOLD}Global{Colors.RESET} {Colors.GREEN}PASSED{Colors.RESET} {passed}/{test}")
    else:
        for i in config:
            if i == "config":
                continue
            passed += runTests(i)
            test += len(config[i]['test_files'])
        print(f"Test {Colors.BOLD}Global{Colors.RESET} {Colors.GREEN}PASSED{Colors.RESET} {passed}/{test}")


class Flags:
    def __init__(self, *arg):
        self.short = set()
        self.long = set()
        self.args = set()
        for i in arg:
            if i.startswith("--") and len(i) > 2:
                self.long.add(i[2:])
            elif i.startswith("-"):
                for j in i[1:]: self.short.add(j)
            elif i:
                self.args.add(i)

    def __getitem__(self, key, which=None):
        if which == None:
            if key in self.long:
                return True
            if key in self.short:
                return True
            return False
        if which == "long":
            return key in self.long
        if which == "short":
            return key in self.short
        return False

    def isEmpty(self):
        return not self.long and not self.short and not self.args

    def isArgs(self):
        return self.args

def printListOfTest(*arg):
    flags = Flags(*arg)
    if flags.isEmpty():
        print(*[i for i in config if i != "config"], sep="\t")
        return
    allConf = [i for i in config if flags["a"] or i != "config" or i in flags.isArgs()]
    if flags.isArgs():
        allConf = [i for i in allConf if i in flags.isArgs()]
    if flags["l"]:
        for i in allConf:
            print(f"{i}:")
            for j in config[i]:
                print(f"    {j}: {config[i][j]}")
            print()
    else:
        print(*allConf, sep="\t")


def addTest(*arg):
    tests_name = ""
    test_files = []
    options = {"-n": None, "-l": None}
    if not os.listdir(testDir):
        print("We Don't have test files to add")
        return
    while (tests_name := input("Choose a name: ").strip()) == "config" or tests_name in config or not tests_name:
        if not tests_name:
            print("Name can't be empty")
        else:
            print(f"{tests_name}: already exist")
    while (tmp := input("Choose files: ").strip()):
        tmp = tmp.split()
        for i in tmp:
            if not os.path.isfile(f"{testDir}/{i}"):
                print(f"{i}: is not a valid file")
                continue
        else:
            test_files += tmp
            break
    while (tmp := input("Choose options -n : ").strip()):
        if tmp.isdigit():
            options["-n"] = int(tmp)
            break
        print(f"{tmp}: is not a valid number")
    while (tmp := input("Choose options -l : ").strip()):
        if tmp.count(".") < 2 and tmp.replace(".", "").isdigit():
            options["-l"] = float(tmp)
            break
        print(f"{tmp}: is not a valid number")
    average = None
    while (tmp := input("Do you want create a average [y/N]: ")):
        if tmp == "y" or tmp == "Y":
            while (tmp := input("Choose the number of average: ")):
                if tmp.isdigit():
                    average = int(tmp)
                    break
                print(f"{tmp}: is not a valid number")
            break
        elif tmp == "N" or tmp == "n" or tmp == "":
            break
        print(f"{tmp}: invalid entry")
    if average:
        config[tests_name] = {"test_name": tests_name, "test_files": test_files, "average": average, **options}
    else:
        config[tests_name] = {"test_name": tests_name, "test_files": test_files, **options}

def rmTest(*arg):
    if not arg:
        print("You must choose a test to remove")
        return
    for i in arg:
        if i in config and i != "config":
            del config[i]
        else:
            if i == "config":
                print(f"{i}: can't be removed")
            else:
                print(f"{i}: not found")


def availableTests(*arg):
    print(*os.listdir(testDir), sep="\t")


def saveConfig(*arg):
    if not arg:
        print("You must choose a file to save")
        return
    if len(arg) > 1:
        print("You can only save one file")
        return
    if not arg[0].endswith(".toml"):
        print("File must be a toml file")
        return
    with open(arg[0], "w") as f:
        toml.dump(config, f)


PROMPT = f"{Colors.BOLD}{Colors.CYAN}Bench -> [Veco] {Colors.WHITE}>{Colors.RESET} "

def cliTests():
    # All commands must be a variadic function
    commands = {"ls":printListOfTest,
                "run":processTests,
                "add":addTest,
                "rm":rmTest,
                "avlbl":availableTests,
                "save":saveConfig }
    while (i := input(PROMPT).strip()) != "exit":
        i = i.split()
        if not i or not i[0] in commands:
            if i:
                print(f"{i[0]}: Commands not found.")
            continue
        commands[i[0]](*i[1:])

if args.cli:
    cliTests()
else:
    processTests()