import os
from modules.annotator import Annotator
from modules.tokenizer import Tokenizer
import argparse
from tqdm import tqdm
from multiprocessing import Pool
from opencc import OpenCC
from collections import Counter
import json

os.environ["TOKENIZERS_PARALLELISM"] = "false"

annotator, sentence_to_tokenized = None, None
cc = OpenCC("t2s")


def annotate(line):
    """
    :param line:
    :return:
    """
    sent_list = line.split("\t")[1:]
    source = sent_list[0]
    if args.segmented:
        source = source.strip()
    else:
        source = "".join(source.strip().split())
    output_str = ""
    for idx, target in enumerate(sent_list[1:]):
        try:
            if args.segmented:
                target = target.strip()
            else:
                target = "".join(target.strip().split())
            if not args.no_simplified:
                target = cc.convert(target)
            source_tokenized, target_tokenized = sentence_to_tokenized[
                source], sentence_to_tokenized[target]
            out, cors = annotator(source_tokenized, target_tokenized, idx)
            if idx == 0:
                output_str += "".join(out[:-1])
            else:
                output_str += "".join(out[1:-1])
        except Exception:
            raise Exception
    return output_str


def simplify_edits(sent, max_answer_num):
    out_edits = []
    # Get the edit lines from an m2 block.
    edits = sent.split("\n")
    # Loop through the edits
    for edit in edits:
        # Preprocessing
        if edit.startswith("A "):
            edit = edit[2:].split("|||")  # Ignore "A " then split.
            span = edit[0].split()
            start = int(span[0])
            end = int(span[1])
            cat = edit[1]
            cor = edit[2].replace(" ", "")
            coder = int(edit[-1])
            out_edit = [start, end, cat, cor, coder]
            out_edits.append(out_edit)
    # return [edit for edit in out_edits if edit[-1] in [0,1]]
    if max_answer_num is None:
        return out_edits
    elif max_answer_num == 1:
        return [edit for edit in out_edits if edit[-1] == 0]
    else:
        return [
            edit for edit in out_edits
            if edit[-1] in list(range(max_answer_num))
        ]


def process_edits(edits, args):
    coder_dict = {}
    # Add an explicit noop edit if there are no edits.
    if not edits:
        edits = [[-1, -1, "noop", "-NONE-", 0]]
    # Loop through the edits
    for edit in edits:
        # Name the edit elements for clarity
        start = edit[0]
        end = edit[1]
        cat = edit[2]
        cor = edit[3]
        coder = edit[4]
        # Add the coder to the coder_dict if necessary
        if coder not in coder_dict:
            coder_dict[coder] = {}

        # Optionally apply filters based on args
        # 1. UNK type edits are only useful for detection, not correction.
        if not args.dt and not args.ds and cat == "UNK":
            continue
        # 2. Only evaluate single token edits; i.e. 0:1, 1:0 or 1:1
        if args.single and (end - start >= 2 or len(cor.split()) >= 2):
            continue
        # 3. Only evaluate multi token edits; i.e. 2+:n or n:2+
        if args.multi and end - start < 2 and len(cor.split()) < 2:
            continue
        # 4. If there is a filter, ignore the specified error types
        if args.filt and cat in args.filt:
            continue

        # Token Based Detection
        if args.dt:
            # Preserve noop edits.
            if start == -1:
                if (start, start) in coder_dict[coder].keys():
                    coder_dict[coder][(start, start)].append(cat)
                else:
                    coder_dict[coder][(start, start)] = [cat]
            # Insertions defined as affecting the token on the right
            elif start == end and start >= 0:
                if (start, start + 1) in coder_dict[coder].keys():
                    coder_dict[coder][(start, start + 1)].append(cat)
                else:
                    coder_dict[coder][(start, start + 1)] = [cat]
            # Edit spans are split for each token in the range.
            else:
                for tok_id in range(start, end):
                    if (tok_id, tok_id + 1) in coder_dict[coder].keys():
                        coder_dict[coder][(tok_id, tok_id + 1)].append(cat)
                    else:
                        coder_dict[coder][(tok_id, tok_id + 1)] = [cat]

        # Span Based Detection
        elif args.ds:
            if (start, end) in coder_dict[coder].keys():
                coder_dict[coder][(start, end)].append(cat)
            else:
                coder_dict[coder][(start, end)] = [cat]

        # Span Based Correction
        else:
            # With error type classification
            if args.cse:
                if (start, end, cat, cor) in coder_dict[coder].keys():
                    coder_dict[coder][(start, end, cat, cor)].append(cat)
                else:
                    coder_dict[coder][(start, end, cat, cor)] = [cat]
            # Without error type classification
            else:
                if (start, end, cor) in coder_dict[coder].keys():
                    coder_dict[coder][(start, end, cor)].append(cat)
                else:
                    coder_dict[coder][(start, end, cor)] = [cat]
    return coder_dict


def evaluate_edits(src, hyp_dict, ref_dict, best, sent_id, args):
    # Store the best sentence level scores and hyp+ref combination IDs
    # best_f is initialised as -1 cause 0 is a valid result.
    best_tp, best_fp, best_fn, best_f, best_hyp, best_ref = 0, 0, 0, -1, 0, 0
    best_cat = {}
    # skip not annotatable sentence
    if len(ref_dict.keys()) == 1:
        ref_id = list(ref_dict.keys())[0]
        if len(ref_dict[ref_id].keys()) == 1:
            cat = list(ref_dict[ref_id].values())[0][0]
            if cat == "NA":
                best_dict = {"tp": best_tp, "fp": best_fp, "fn": best_fn}
                return best_dict, best_cat

    # Compare each hyp and ref combination
    for hyp_id in hyp_dict.keys():
        for ref_id in ref_dict.keys():
            # Get the local counts for the current combination.
            tp, fp, fn, cat_dict = compareEdits(hyp_dict[hyp_id],
                                                ref_dict[ref_id])
            # Compute the local sentence scores (for verbose output only)
            loc_p, loc_r, loc_f = computeFScore(tp, fp, fn, args.beta)
            # Compute the global sentence scores
            p, r, f = computeFScore(tp + best["tp"], fp + best["fp"],
                                    fn + best["fn"], args.beta)
            # Save the scores if they are better in terms of:
            # 1. Higher F-score
            # 2. Same F-score, higher TP
            # 3. Same F-score and TP, lower FP
            # 4. Same F-score, TP and FP, lower FN
            if (f > best_f) or \
                    (f == best_f and tp > best_tp) or \
                    (f == best_f and tp == best_tp and fp < best_fp) or \
                    (f == best_f and tp == best_tp and fp == best_fp
                        and fn < best_fn):
                best_tp, best_fp, best_fn = tp, fp, fn
                best_f, best_hyp, best_ref = f, hyp_id, ref_id
                best_cat = cat_dict
            # Verbose output
            if args.verbose:
                # Prepare verbose output edits.
                hyp_verb = list(sorted(hyp_dict[hyp_id].keys()))
                ref_verb = list(sorted(ref_dict[ref_id].keys()))
                # Ignore noop edits
                if not hyp_verb or hyp_verb[0][0] == -1:
                    hyp_verb = []
                if not ref_verb or ref_verb[0][0] == -1:
                    ref_verb = []
                # Print verbose info
                print('{:-^40}'.format(""))
                print("SENTENCE " + str(sent_id) + src[1:])
                print('{:-^40}'.format(""))
                print("SENTENCE " + str(sent_id) + " - HYP " + str(hyp_id) +
                      " - REF " + str(ref_id))
                print("HYPOTHESIS EDITS :", hyp_verb)
                print("REFERENCE EDITS  :", ref_verb)
                print("Local TP/FP/FN   :", str(tp), str(fp), str(fn))
                print("Local P/R/F" + str(args.beta) + "  :", str(loc_p),
                      str(loc_r), str(loc_f))
                print("Global TP/FP/FN  :", str(tp + best["tp"]),
                      str(fp + best["fp"]), str(fn + best["fn"]))
                print("Global P/R/F" + str(args.beta) + "  :", str(p), str(r),
                      str(f))
    # Verbose output: display the best hyp+ref combination
    if args.verbose:
        print('{:-^40}'.format(""))
        print("^^ HYP " + str(best_hyp) + ", REF " + str(best_ref) +
              " chosen for sentence " + str(sent_id))
    # Save the best TP, FP and FNs as a dict,
    # and return this and the best_cat dict
    best_dict = {"tp": best_tp, "fp": best_fp, "fn": best_fn}
    return best_dict, best_cat


def compareEdits(hyp_edits, ref_edits):
    tp = 0  # True Positives
    fp = 0  # False Positives
    fn = 0  # False Negatives
    cat_dict = {}  # {cat: [tp, fp, fn], ...}

    for h_edit, h_cats in hyp_edits.items():
        # noop hyp edits cannot be TP or FP
        if h_cats[0] == "noop":
            continue
        # TRUE POSITIVES
        if h_edit in ref_edits.keys():
            # On occasion, multiple tokens at same span.
            for h_cat in ref_edits[h_edit]:  # Use ref dict for TP
                tp += 1
                # Each dict value [TP, FP, FN]
                if h_cat in cat_dict.keys():
                    cat_dict[h_cat][0] += 1
                else:
                    cat_dict[h_cat] = [1, 0, 0]
        # FALSE POSITIVES
        else:
            # On occasion, multiple tokens at same span.
            for h_cat in h_cats:
                fp += 1
                # Each dict value [TP, FP, FN]
                if h_cat in cat_dict.keys():
                    cat_dict[h_cat][1] += 1
                else:
                    cat_dict[h_cat] = [0, 1, 0]
    for r_edit, r_cats in ref_edits.items():
        # noop ref edits cannot be FN
        if r_cats[0] == "noop":
            continue
        # FALSE NEGATIVES
        if r_edit not in hyp_edits.keys():
            # On occasion, multiple tokens at same span.
            for r_cat in r_cats:
                fn += 1
                # Each dict value [TP, FP, FN]
                if r_cat in cat_dict.keys():
                    cat_dict[r_cat][2] += 1
                else:
                    cat_dict[r_cat] = [0, 0, 1]
    return tp, fp, fn, cat_dict


# Input 1-3: True positives, false positives, false negatives
# Input 4: Value of beta in F-score.
# Output 1-3: Precision, Recall and F-score rounded to 4dp.
def computeFScore(tp, fp, fn, beta):
    p = float(tp) / (tp + fp) if fp else 1.0
    r = float(tp) / (tp + fn) if fn else 1.0
    f = float(
        (1 + (beta**2)) * p * r) / (((beta**2) * p) + r) if p + r else 0.0
    return round(p, 4), round(r, 4), round(f, 4)


# Input 1-2: Two error category dicts. Key is cat, value is list of TP, FP, FN.
# Output: The dictionaries combined with cumulative TP, FP, FN.
def merge_dict(dict1, dict2):
    for cat, stats in dict2.items():
        if cat in dict1.keys():
            dict1[cat] = [x + y for x, y in zip(dict1[cat], stats)]
        else:
            dict1[cat] = stats
    return dict1


# Input 1: A dict; key is error cat, value is counts for [tp, fp, fn]
# Input 2: Integer value denoting level of error category granularity.
# 1: Operation tier; e.g. M, R, U.
# 2: Main tier; e.g. NOUN, VERB  3: Everything.
# Output: A dictionary of category TP, FP and FN based on Input 2.
def processCategories(cat_dict, setting):
    # Otherwise, do some processing.
    proc_cat_dict = {}
    for cat, cnt in cat_dict.items():
        if cat == "UNK":
            proc_cat_dict[cat] = cnt
            continue
        # M, U, R or UNK combined only.
        if setting == 1:
            if cat[0] in proc_cat_dict.keys():
                proc_cat_dict[cat[0]] = [
                    x + y for x, y in zip(proc_cat_dict[cat[0]], cnt)
                ]
            else:
                proc_cat_dict[cat[0]] = cnt
        # Everything without M, U or R.
        elif setting == 2:
            if cat[2:] in proc_cat_dict.keys():
                proc_cat_dict[cat[2:]] = [
                    x + y for x, y in zip(proc_cat_dict[cat[2:]], cnt)
                ]
            else:
                proc_cat_dict[cat[2:]] = cnt
        # All error category combinations
        else:
            return cat_dict
    return proc_cat_dict


# Input 1: A dict of global best TP, FP and FNs
# Input 2: A dict of error types and counts for those TP, FP and FNs
# Input 3: Command line args
def print_results(best, best_cats, args):
    # Prepare output title.
    if args.dt:
        title = " Token-Based Detection "
    elif args.ds:
        title = " Span-Based Detection "
    elif args.cse:
        title = " Span-Based Correction + Classification "
    else:
        title = " Span-Based Correction "

    # Category Scores
    if args.cat:
        best_cats = processCategories(best_cats, args.cat)
        #print("")
        #print('{:=^66}'.format(title))
        #print("Category".ljust(14), "TP".ljust(8), "FP".ljust(8),
              #"FN".ljust(8), "P".ljust(8), "R".ljust(8), "F" + str(args.beta))
        for cat, cnts in sorted(best_cats.items()):
            cat_p, cat_r, cat_f = computeFScore(cnts[0], cnts[1], cnts[2],
                                                args.beta)
        result_dict = {
            "Category": cat,
            "Precision": cat_p,
            "Recall": cat_r,
            "F0.5": cat_f,
            }
            #print(cat.ljust(14),
                  #str(cnts[0]).ljust(8),
                  #str(cnts[1]).ljust(8),
                  #str(cnts[2]).ljust(8),
                  #str(cat_p).ljust(8),
                  #str(cat_r).ljust(8), cat_f)
    else:
        prec, rec, f = computeFScore(best['tp'], best['fp'], best['fn'], args.beta)
        result_dict = {
            "Precision": prec,
            "Recall": rec,
            "F0.5": f,
            }
    # Print the overall results.
    #print("")
    #print('{:=^46}'.format(title))
    #print("\t".join(["TP", "FP", "FN", "Prec", "Rec", "F" + str(args.beta)]))
    #print("\t".join(
        #map(str, [best["tp"], best["fp"], best["fn"]] + list(
            #computeFScore(best["tp"], best["fp"], best["fn"], args.beta)))))
    #print('{:=^46}'.format(""))
    #print("")
    with open('scores.json', 'w') as fw:
        fw.write(json.dumps(result_dict, indent=4))


def main(args):
    tokenizer = Tokenizer(args.granularity, args.device, args.segmented)
    global annotator, sentence_to_tokenized
    annotator = Annotator.create_default(args.granularity,
                                         args.multi_cheapest_strategy)
    lines = open(args.file,
                 "r").read().strip().split("\n")  # format: id src tgt1 tgt2...
    # error_types = []

    # with open(args.output, "w") as f:
    hyp_m2 = []
    count = 0
    sentence_set = set()
    sentence_to_tokenized = {'': ''}
    for line in lines:
        sent_list = line.split("\t")[1:]
        # sent_list = line.split("\t")
        for idx, sent in enumerate(sent_list):
            if args.segmented:
                # print(sent)
                sent = sent.strip()
            else:
                sent = "".join(sent.split()).strip()
            if idx >= 1:
                if not args.no_simplified:
                    sentence_set.add(cc.convert(sent))
                else:
                    sentence_set.add(sent)
            else:
                sentence_set.add(sent)
    batch = []
    for sent in tqdm(sentence_set):
        count += 1
        if sent:
            batch.append(sent)
        if count % args.batch_size == 0:
            results = tokenizer(batch)
            for s, r in zip(batch, results):
                sentence_to_tokenized[s] = r  # Get tokenization map.
            batch = []
    if batch:
        results = tokenizer(batch)
        for s, r in zip(batch, results):
            sentence_to_tokenized[s] = r  # Get tokenization map.
    with Pool(args.worker_num) as pool:
        for ret in pool.imap(annotate, tqdm(lines), chunksize=8):
            if ret:
                hyp_m2.append(ret)

    ref_m2 = open(args.ref).read().strip().split("\n\n")
    # Make sure they have the same number of sentences
    assert len(hyp_m2) == len(ref_m2), print(len(hyp_m2), len(ref_m2))

    # Store global corpus level best counts here
    best_dict = Counter({"tp": 0, "fp": 0, "fn": 0})
    best_cats = {}
    # Process each sentence
    sents = zip(hyp_m2, ref_m2)
    for sent_id, sent in enumerate(sents):
        # Simplify the edits into lists of lists
        # if "A1" in sent[0] or "A1" in sent[1] or sent_id in sent_id_cons:
        #     sent_id_cons.append(sent_id)
        src = sent[0].split("\n")[0]
        hyp_edits = simplify_edits(sent[0], args.max_answer_num)
        ref_edits = simplify_edits(sent[1], args.max_answer_num)
        # Process the edits for detection/correction based on args
        hyp_dict = process_edits(hyp_edits, args)
        ref_dict = process_edits(ref_edits, args)
        if args.reference_num is None or len(
                ref_dict.keys()) == args.reference_num:
            # Evaluate edits and get best TP, FP, FN hyp+ref combo.
            count_dict, cat_dict = evaluate_edits(src, hyp_dict, ref_dict,
                                                  best_dict, sent_id, args)
            # Merge these dicts with best_dict and best_cats
            best_dict += Counter(count_dict)
            best_cats = merge_dict(best_cats, cat_dict)
    # Print results
    print_results(best_dict, best_cats, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Choose input file to annotate")
    parser.add_argument("-f",
                        "--file",
                        type=str,
                        required=True,
                        help="Input parallel file")
    # parser.add_argument("-o",
    #                     "--output",
    #                     type=str,
    #                     help="Output file",
    #                     required=True)
    parser.add_argument("-r",
                        "--ref",
                        help="A reference M2 file.",
                        required=True)
    parser.add_argument("-b",
                        "--batch_size",
                        type=int,
                        help="The size of batch",
                        default=128)
    parser.add_argument("-d",
                        "--device",
                        type=int,
                        help="The ID of GPU",
                        default=0)
    parser.add_argument("-w",
                        "--worker_num",
                        type=int,
                        help="The number of workers",
                        default=16)
    parser.add_argument("-g",
                        "--granularity",
                        type=str,
                        help="Choose char-level or word-level evaluation",
                        default="char")
    parser.add_argument(
        "-m",
        "--merge",
        help="Whether merge continuous replacement/deletion/insertion",
        action="store_true")
    parser.add_argument("-s",
                        "--multi_cheapest_strategy",
                        type=str,
                        choices=["first", "all"])
    parser.add_argument("--segmented",
                        help="Whether tokens have been segmented",
                        action="store_true")  # 支持提前token化，用空格隔开
    parser.add_argument("--no_simplified",
                        help="Whether simplifying chinese",
                        action="store_true")  # 将所有corrections转换为简体中文
    parser.add_argument("--max_answer_num", type=int, default=None)
    parser.add_argument("--reference_num", type=int, default=None)
    parser.add_argument("--beta",
                        help="Value of beta in F-score. (default: 0.5)",
                        default=0.5,
                        type=float)
    parser.add_argument("-v",
                        "--verbose",
                        help="Print verbose output.",
                        action="store_true")
    eval_type = parser.add_mutually_exclusive_group()
    eval_type.add_argument("-dt",
                           help="Evaluate Detection in terms of Tokens.",
                           action="store_true")
    eval_type.add_argument("-ds",
                           help="Evaluate Detection in terms of Spans.",
                           action="store_true")
    eval_type.add_argument(
        "-cs",
        help="Evaluate Correction in terms of Spans. (default)",
        action="store_true")
    eval_type.add_argument(
        "-cse",
        help="Evaluate Correction in terms of Spans and Error types.",
        action="store_true")
    parser.add_argument(
        "-single",
        help="Only evaluate single token edits; i.e. 0:1, 1:0 or 1:1",
        action="store_true")
    parser.add_argument(
        "-multi",
        help="Only evaluate multi token edits; i.e. 2+:n or n:2+",
        action="store_true")
    parser.add_argument(
        "-multi_hyp_avg",
        help="When get multiple hypotheses for a sentence, calculate "
        "their average F-scores for this sentence.",
        action="store_true")  # For IAA calculation
    parser.add_argument(
        "-multi_hyp_max",
        help="When get multiple hypotheses for a sentence, calculate "
        "their F-scores and select the max one for this sentence.",
        action="store_true")  # For multiple hypotheses system evaluation
    parser.add_argument("-filt",
                        help="Do not evaluate the specified error types.",
                        nargs="+",
                        default=[])
    parser.add_argument("-cat",
                        help="Show error category scores.\n"
                        "1: Only show operation tier scores; e.g. R.\n"
                        "2: Only show main tier scores; e.g. NOUN.\n"
                        "3: Show all category scores; e.g. R:NOUN.",
                        choices=[1, 2, 3],
                        type=int)
    args = parser.parse_args()
    main(args)
