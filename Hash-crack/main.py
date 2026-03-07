import argparse


def parse_arguments():
    # TODO: use argparse to get:
    # --hash
    # --algorithm
    # --wordlist
    # --mode (dictionary/bruteforce)
    # --charset
    # --max-length
    # --salt

    parser = argparse.ArgumentParser(description="Hash cracking tool")
    parser.add_argument("--hash", required=True, help="The hash to crack")
    parser.add_argument("--algorithm", required=True, choices=["md5", "sha1", "sha256"], help="Hashing algorithm")
    parser.add_argument("--mode", required=True, choices=["dictionary", "bruteforce"], help="Attack mode")
    parser.add_argument("--wordlist", help="Path to the wordlist for dictionary attack")
    parser.add_argument("--charset", help="Character set for brute-force attack")
    parser.add_argument("--max-length", type=int, help="Maximum password length for brute-force attack")
    parser.add_argument("--salt", default="", help="Salt value to use in hashing")
    pass

def main():
    # TODO: parse args
    # TODO: route to dictionary or brute-force attack
    # TODO: print results
    pass

if __name__ == "__main__":
    main()
