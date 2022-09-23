import argparse

def main(args):
    para = []
    s = open(args.src_path,"r").readlines()
    t = open(args.tgt_path,"r").readlines()
    output = open(args.file,"w")
    for line in range(len(s)):
        s[line]=''.join(s[line].split())
        s[line]=s[line].lstrip(str(line))
        t[line]=t[line].lstrip(str(line))
        para.append(str(line)+"\t"+s[line].strip("\n")+"\t"+t[line].strip("\n")+"\n")
    
    [output.write(str(item)) for item in para]
    output.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Choose input file to annotate")
    parser.add_argument("-f",
                        "--file",
                        type=str,
                        required=True,
                        help="output test file")
    parser.add_argument("-s",
                        "--src_path",
                        type=str,
                        required=True,)
    parser.add_argument("-t",
                        "--tgt_path",
                        type=str,
                        required=True,
                       )
    args = parser.parse_args()
    main(args)