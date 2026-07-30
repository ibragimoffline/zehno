#!/bin/sh
#
# Zehno.uz - repozitoriyada maxfiy ma'lumot bor-yo'qligini tekshiradi.
#
#   ./scripts/scan-secrets.sh            # barcha kuzatilayotgan fayllar
#   ./scripts/scan-secrets.sh --staged   # faqat commit'ga tayyorlangan fayllar
#   ./scripts/scan-secrets.sh --history  # git tarixi (push qilingan commitlar)
#
# Chiqish kodi: 0 - toza, 1 - sir topildi.
#
# Bu skript .githooks/pre-commit tomonidan ham chaqiriladi.

set -eu

MODE="${1:---all}"
TMP="${TMPDIR:-/tmp}"
NAME_HITS="$TMP/zehno-names.$$"
BODY_HITS="$TMP/zehno-body.$$"
: > "$NAME_HITS"
: > "$BODY_HITS"
trap 'rm -f "$NAME_HITS" "$BODY_HITS"' EXIT

SKIP='change-me|changeme|your-|your_|example|placeholder|xxxxx|dummy|sample|fake|<[A-Za-z_]|\.\.\.|dev_password|zehno_minio|REPLACE|TODO'

# --------------------------------------------------------------- tarix rejimi
if [ "$MODE" = "--history" ]; then
    echo "Git tarixi tekshirilmoqda..."
    found=0
    for pattern in \
        '[0-9]\{8,11\}:AA[A-Za-z0-9_-]\{30,\}' \
        'AKIA[0-9A-Z]\{16\}' \
        'BEGIN [A-Z ]*PRIVATE KEY' \
        'gh[pousr]_[A-Za-z0-9]\{30,\}'
    do
        hits=$(git log --all -G"$pattern" --oneline 2>/dev/null | head -5 || true)
        if [ -n "$hits" ]; then
            echo "  TOPILDI: $pattern"
            echo "$hits" | sed 's/^/    /'
            found=1
        fi
    done
    envs=$(git log --all --name-only --pretty=format: 2>/dev/null | sort -u | grep -E '(^|/)\.env$' || true)
    if [ -n "$envs" ]; then
        echo "  TOPILDI: tarixda .env fayli bor"
        echo "$envs" | sed 's/^/    /'
        found=1
    fi
    if [ "$found" -eq 0 ]; then
        echo "Tarix toza - sir topilmadi."
        exit 0
    fi
    echo ""
    echo "Tarixdagi sirni olib tashlash uchun git-filter-repo ishlating va"
    echo "kalitni provayderda ALBATTA almashtiring (u allaqachon oshkor bo'lgan)."
    exit 1
fi

# --------------------------------------------------------------- fayllar ro'yxati
if [ "$MODE" = "--staged" ]; then
    FILES=$(git diff --cached --name-only --diff-filter=ACMR || true)
    READ_CMD="staged"
else
    FILES=$(git ls-files || true)
    READ_CMD="worktree"
fi
[ -z "$FILES" ] && exit 0

read_file() {
    if [ "$READ_CMD" = "staged" ]; then
        git show ":$1" 2>/dev/null || true
    else
        cat "$1" 2>/dev/null || true
    fi
}

# --------------------------------------------------------------- fayl nomlari
echo "$FILES" | while IFS= read -r f; do
    [ -z "$f" ] && continue
    base=$(basename "$f")
    case "$base" in
        .env.example|*.env.example) continue ;;
    esac
    case "$base" in
        .env|.env.*|*.env)                     echo "$f|muhit fayli (.env)" >> "$NAME_HITS" ;;
        *.pem|*.key|*.p12|*.pfx|*.jks)         echo "$f|kalit yoki sertifikat" >> "$NAME_HITS" ;;
        *.keystore|*.ppk)                      echo "$f|kalit ombori" >> "$NAME_HITS" ;;
        id_rsa*|id_dsa*|id_ecdsa*|id_ed25519*) echo "$f|SSH maxfiy kaliti" >> "$NAME_HITS" ;;
        credentials|credentials.json)          echo "$f|hisob ma'lumotlari" >> "$NAME_HITS" ;;
        service-account*.json|firebase-adminsdk*.json) echo "$f|servis hisobi" >> "$NAME_HITS" ;;
        .netrc|.pgpass)                        echo "$f|parol fayli" >> "$NAME_HITS" ;;
        *.secret|secrets.yml|secrets.yaml|*-secrets.yml|*-secrets.yaml) echo "$f|sir fayli" >> "$NAME_HITS" ;;
    esac
done || true

# --------------------------------------------------------------- fayl mazmuni
scan() {
    regex="$1"
    label="$2"
    echo "$FILES" | while IFS= read -r f; do
        [ -z "$f" ] && continue
        case "$(basename "$f")" in
            *.png|*.jpg|*.jpeg|*.gif|*.webp|*.ico|*.pdf|*.mp4|*.zip|*.woff|*.woff2) continue ;;
            package-lock.json|pnpm-lock.yaml|yarn.lock) continue ;;
        esac
        hit=$(read_file "$f" | grep -nE -e "$regex" 2>/dev/null | grep -vE -e "$SKIP" | head -1 || true)
        if [ -n "$hit" ]; then
            echo "$f|$label|$(echo "$hit" | cut -c1-100)" >> "$BODY_HITS"
        fi
    done
    return 0
}

scan '[0-9]{8,11}:AA[A-Za-z0-9_-]{30,}'                                   'Telegram bot token'
scan 'bitrix24\.[a-z]{2,4}/rest/[0-9]+/[A-Za-z0-9]{8,}'                   'Bitrix24 webhook kaliti'
scan 'AKIA[0-9A-Z]{16}'                                                   'AWS access key'
scan '-----BEGIN [A-Z ]*PRIVATE KEY-----'                                 'Private key bloki'
scan 'eyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}'   'JWT token'
scan 'gh[pousr]_[A-Za-z0-9]{30,}'                                         'GitHub token'
scan 'sk-[A-Za-z0-9]{32,}'                                                'API kaliti (sk-)'
scan 'xox[baprs]-[A-Za-z0-9-]{20,}'                                       'Slack token'
scan '(SECRET|PASSWORD|TOKEN|API_?KEY|WEBHOOK_URL)[A-Z_]*[[:space:]]*[:=][[:space:]]*.?[A-Za-z0-9+/=_-]{24,}' 'Uzun kalit/parol qiymati'

# --------------------------------------------------------------- natija
if [ ! -s "$NAME_HITS" ] && [ ! -s "$BODY_HITS" ]; then
    [ "$MODE" != "--staged" ] && echo "Toza - $(echo "$FILES" | wc -l) faylda sir topilmadi."
    exit 0
fi

echo ""
echo "=============================================================="
if [ "$MODE" = "--staged" ]; then
    echo "  COMMIT TO'XTATILDI - maxfiy ma'lumot aniqlandi"
else
    echo "  MAXFIY MA'LUMOT ANIQLANDI"
fi
echo "=============================================================="
echo ""

if [ -s "$NAME_HITS" ]; then
    echo "Taqiqlangan fayllar:"
    while IFS='|' read -r f why; do
        [ -n "$f" ] && echo "  * $f  ($why)"
    done < "$NAME_HITS"
    echo ""
fi

if [ -s "$BODY_HITS" ]; then
    echo "Fayl ichidagi sirlar:"
    while IFS='|' read -r f label hit; do
        [ -n "$f" ] && { echo "  * $f  ->  $label"; echo "      $hit"; }
    done < "$BODY_HITS"
    echo ""
fi

echo "Nima qilish kerak:"
echo "  1. Sirni fayldan olib tashlang, .env ga ko'chiring"
echo "  2. Indeksdan chiqaring:  git restore --staged <fayl>"
echo "  3. Kalit oshkor bo'lgan bo'lsa - provayderda ALMASHTIRING"
echo ""
exit 1
