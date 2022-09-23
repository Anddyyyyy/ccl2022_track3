import argparse

def main(args):
    src = []
    tgt = []
    with open(args.file,"r") as f:
        for line in f.readlines():
            line = line.strip("\n")
            line = line.split()
            for t in line[2:]:
                src.append(' '.join(line[1]))
                tgt.append(' '.join(t))
            # data.append(line)
    with open(args.src_path,'w') as s:
        [s.write(str(item)+'\n') for  item in src]
        s.close()
    
    with open(args.tgt_path,'w') as t:
        [t.write(str(item)+'\n') for  item in tgt]
        t.close()
    
            
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Choose input file to annotate")
    parser.add_argument("-f",
                        "--file",
                        type=str,
                        required=True,
                        help="Input parallel file")
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