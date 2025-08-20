#!/usr/bin/env python3
"""
Скрипт для проверки безопасности Shop-bot
Проверяет зависимости, версии и потенциальные уязвимости
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple


def run_command(command: str) -> Tuple[int, str, str]:
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(
            command.split(), capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_pip_list() -> Dict[str, str]:
    """Получает список установленных пакетов"""
    code, stdout, stderr = run_command("pip list --format=json")
    if code != 0:
        print(f"Ошибка получения списка пакетов: {stderr}")
        return {}

    try:
        packages = json.loads(stdout)
        return {pkg["name"]: pkg["version"] for pkg in packages}
    except json.JSONDecodeError:
        print("Ошибка парсинга JSON")
        return {}


def check_outdated_packages() -> List[str]:
    """Проверяет устаревшие пакеты"""
    code, stdout, stderr = run_command("pip list --outdated")
    if code != 0:
        return []

    outdated = []
    for line in stdout.strip().split("\n")[2:]:  # Пропускаем заголовки
        if line.strip():
            package = line.split()[0]
            outdated.append(package)

    return outdated


def check_security_issues() -> Dict[str, List[str]]:
    """Проверяет известные проблемы безопасности"""
    issues = {"critical": [], "high": [], "medium": [], "low": []}

    # Проверяем Jinja2
    packages = check_pip_list()
    if "jinja2" in packages:
        version = packages["jinja2"]
        if version < "3.1.6":
            issues["critical"].append(
                f"Jinja2 {version} - уязвим к CVE-2024-56326, CVE-2024-56201, CVE-2025-27516, CVE-2024-34064"
            )

    # Проверяем python-dotenv
    if "python-dotenv" in packages:
        version = packages["python-dotenv"]
        if version < "1.1.1":
            issues["high"].append(
                f"python-dotenv {version} - рекомендуется обновить до 1.1.1+"
            )

    # Проверяем aiohttp
    if "aiohttp" in packages:
        version = packages["aiohttp"]
        if version < "3.12.0":
            issues["medium"].append(
                f"aiohttp {version} - рекомендуется обновить до 3.12.0+"
            )

    return issues


def check_code_security() -> List[str]:
    """Проверяет код на потенциальные проблемы безопасности"""
    issues = []

    # Проверяем использование небезопасных методов
    code, stdout, stderr = run_command("grep -r '\.format(' --include='*.py' .")
    if code == 0 and stdout.strip():
        issues.append("Обнаружено использование .format() - проверьте на безопасность")

    code, stdout, stderr = run_command("grep -r 'str\.format' --include='*.py' .")
    if code == 0 and stdout.strip():
        issues.append("Обнаружено использование str.format - проверьте на безопасность")

    # Проверяем eval/exec
    code, stdout, stderr = run_command("grep -r -E '(eval|exec)' --include='*.py' .")
    if code == 0 and stdout.strip():
        issues.append("ОБНАРУЖЕНО ИСПОЛЬЗОВАНИЕ eval/exec - КРИТИЧЕСКАЯ УЯЗВИМОСТЬ!")

    return issues


def main():
    """Основная функция проверки безопасности"""
    print("🔒 Проверка безопасности Shop-bot")
    print("=" * 50)

    # Проверяем зависимости
    print("\n📦 Проверка зависимостей...")
    packages = check_pip_list()
    print(f"Установлено пакетов: {len(packages)}")

    # Проверяем устаревшие пакеты
    outdated = check_outdated_packages()
    if outdated:
        print(f"⚠️  Устаревших пакетов: {len(outdated)}")
        for pkg in outdated[:5]:  # Показываем первые 5
            print(f"   - {pkg}")
        if len(outdated) > 5:
            print(f"   ... и еще {len(outdated) - 5}")
    else:
        print("✅ Все пакеты актуальны")

    # Проверяем проблемы безопасности
    print("\n🛡️  Проверка проблем безопасности...")
    security_issues = check_security_issues()

    total_issues = sum(len(issues) for issues in security_issues.values())
    if total_issues == 0:
        print("✅ Проблем безопасности не обнаружено")
    else:
        print(f"⚠️  Обнаружено проблем: {total_issues}")

        for severity, issues in security_issues.items():
            if issues:
                print(f"\n{severity.upper()}:")
                for issue in issues:
                    print(f"   - {issue}")

    # Проверяем код
    print("\n🔍 Проверка кода...")
    code_issues = check_code_security()
    if code_issues:
        print("⚠️  Потенциальные проблемы в коде:")
        for issue in code_issues:
            print(f"   - {issue}")
    else:
        print("✅ Проблем в коде не обнаружено")

    # Итоговая оценка
    print("\n" + "=" * 50)
    if total_issues == 0 and not code_issues:
        print("🎉 Проект безопасен!")
        return 0
    else:
        print("⚠️  Обнаружены проблемы, требующие внимания")
        return 1


if __name__ == "__main__":
    sys.exit(main())
