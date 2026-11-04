"""Create a disposable Fe test ingot from the independent checked-in vectors."""
import json
import os
from pathlib import Path
from oracle import ROOT, encoded_vectors, self_check


def prepare(destination: Path) -> int:
    self_check()
    payload = encoded_vectors()
    if (ROOT / "fixtures/vectors.json").read_bytes() != payload:
        raise ValueError("Reviewable vectors differ from independent regeneration")
    vectors = json.loads(payload)["cases"]
    source = [
        "// Generated test harness. Never used as the mathematical reference.",
        "use exactsplit::{Units, BasisPoints, TieBreak, SplitResult, preview}",
        "",
        "fn verify_vector(total: u256, weights: [BasisPoints; 16], len: usize,",
        "    mode: TieBreak, cursor: usize, expected: [u256; 16], next_cursor: usize) {",
        "    match preview(amount: Units { value: total }, weights: weights, len: len,",
        "        mode: mode, cursor: cursor) {",
        "        SplitResult::Ok(actual) => {",
        "            assert!(actual.len == len)",
        "            assert!(actual.next_cursor == next_cursor)",
        "            var total_paid: u256 = 0",
        "            var index: usize = 0",
        "            while index < 16 {",
        "                assert!(actual.payouts[index].value == expected[index])",
        "                total_paid = total_paid + actual.payouts[index].value",
        "                index = index + 1",
        "            }",
        "            assert!(total_paid == total)",
        "        }",
        "        SplitResult::Err(_) => assert!(false),",
        "    }",
        "}",
        "",
    ]
    for item in vectors:
        weights = item["weights"] + [0] * (16 - len(item["weights"]))
        payouts = item["payouts"] + ["0"] * (16 - len(item["payouts"]))
        source += [
            "#[test]", f'fn {item["name"]}() {{',
            f'    verify_vector(total: {item["total"]},',
            "        weights: [" + ", ".join(f"BasisPoints {{ value: {w} }}" for w in weights) + "],",
            f'        len: {len(item["weights"])}, mode: TieBreak::{item["mode"]}, cursor: {item["cursor"]},',
            "        expected: [" + ", ".join(payouts) + "],",
            f'        next_cursor: {item["next_cursor"]})', "}", "",
        ]
    (destination / "src").mkdir(parents=True, exist_ok=True)
    relative = Path(os.path.relpath(ROOT, destination)).as_posix()
    manifest = ('[ingot]\nname = "exactsplit_oracle_tests"\nversion = "0.1.0"\n\n'
                f'[dependencies]\nexactsplit = {{ path = "{relative}" }}\n')
    (destination / "fe.toml").write_text(manifest, encoding="utf-8", newline="\n")
    (destination / "src/lib.fe").write_text("\n".join(source), encoding="utf-8", newline="\n")
    return len(vectors)


if __name__ == "__main__":
    target = ROOT / ".artifacts/oracle-tests"
    print(f"Generated {prepare(target)} Fe runtime tests in {target.relative_to(ROOT)}.")
