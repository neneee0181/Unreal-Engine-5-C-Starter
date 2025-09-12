import os
import subprocess

CHUNK_LIMIT_MB = 300
REMOTE = "origin"
BRANCH = "master"
CHUNK_LIMIT = CHUNK_LIMIT_MB * 1024 * 1024

def run_cmd(args):
    """명령어 실행 + 로그"""
    print(f"[실행] {' '.join(args)}")
    result = subprocess.run(args)
    if result.returncode != 0:
        print(f"[오류] {' '.join(args)} (코드 {result.returncode})")
        exit(1)

def get_all_files():
    """저장소 안의 모든 파일(폴더 내부 포함)"""
    files = []
    for root, _, fnames in os.walk("."):
        # .git 폴더는 제외
        if ".git" in root:
            continue
        for name in fnames:
            path = os.path.join(root, name)
            files.append(path)
    print(f"[로그] 전체 파일 수집 완료 → {len(files)}개 파일")
    return files

def get_file_size(file_path):
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def commit_and_push(chunk_num, chunk_files, cur_size):
    size_mb = cur_size / 1024 / 1024
    print(f"\n[커밋 준비] Chunk {chunk_num} → {len(chunk_files)}개 파일, {size_mb:.2f} MB")
    for f in chunk_files:
        print(f"   - {f} ({get_file_size(f)/1024/1024:.2f} MB)")

    # 무조건 add (변경 없어도 강제 스테이징)
    run_cmd(["git", "add", "-f"] + chunk_files)

    # commit은 무조건 강제 (--allow-empty)
    run_cmd(["git", "commit", "--allow-empty", "-m", f"Chunk {chunk_num}"])
    run_cmd(["git", "push", REMOTE, BRANCH])
    print(f"[업로드 완료] Chunk {chunk_num}\n")

def main():
    files = get_all_files()
    if not files:
        print("⚠️ 저장소 안에 파일이 없습니다.")
        return

    chunk_files = []
    cur_size = 0
    chunk_num = 1

    for file in files:
        size = get_file_size(file)

        # 파일별 로그
        print(f"[로그] 파일 추가 후보: {file} ({size/1024/1024:.2f} MB)")

        if cur_size + size > CHUNK_LIMIT and chunk_files:
            print(f"[로그] 용량 초과 → 이전 Chunk {chunk_num} 커밋 실행")
            commit_and_push(chunk_num, chunk_files, cur_size)
            chunk_num += 1
            chunk_files = [file]
            cur_size = size
        else:
            chunk_files.append(file)
            cur_size += size

    if chunk_files:
        commit_and_push(chunk_num, chunk_files, cur_size)

    print("\n✅ 모든 파일이 300MB 단위로 강제 커밋 & 푸시 완료되었습니다!")

if __name__ == "__main__":
    main()
