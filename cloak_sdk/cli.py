"""
CloakAPI CLI — واجهة سطر الأوامر
الاستخدام: python -m cloakapi deploy my_script.py
"""

import sys
import argparse
import json
from pathlib import Path
from . import deploy, list_endpoints, call


def main():
    parser = argparse.ArgumentParser(
        prog="cloakapi",
        description="CloakAPI — حوّل كودك إلى API محمي ومستضاف فورياً",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  cloakapi deploy my_script.py
  cloakapi deploy my_script.py --name "my-api" --desc "حاسبة بسيطة"
  cloakapi list
  cloakapi call ep_abc123 cloak_key_xxx --input '{"x": 5, "y": 10}'
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="الأوامر المتاحة")

    # أمر الرفع
    deploy_parser = subparsers.add_parser("deploy", help="رفع ملف Python كـ API")
    deploy_parser.add_argument("file", help="مسار ملف Python")
    deploy_parser.add_argument("--name", help="اسم مخصص للـ Endpoint", default=None)
    deploy_parser.add_argument("--desc", help="وصف مختصر للـ API", default="")

    # أمر عرض القائمة
    list_parser = subparsers.add_parser("list", help="عرض الـ APIs المرفوعة")

    # أمر الاستدعاء
    call_parser = subparsers.add_parser("call", help="استدعاء API محمي")
    call_parser.add_argument("endpoint_id", help="معرف الـ Endpoint")
    call_parser.add_argument("api_key", help="مفتاح المصادقة")
    call_parser.add_argument("--input", help="المدخلات كـ JSON string", default="{}")

    args = parser.parse_args()

    if args.command == "deploy":
        try:
            result = deploy(args.file, endpoint_name=args.name, description=args.desc)
        except Exception as e:
            print(f"❌ خطأ: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        endpoints = list_endpoints()
        if not endpoints:
            print("لا توجد APIs مرفوعة بعد. استخدم: cloakapi deploy <file.py>")
        else:
            print(f"\n{'='*60}")
            print(f"{'الـ APIs المرفوعة':^60}")
            print(f"{'='*60}")
            for i, ep in enumerate(endpoints, 1):
                print(f"\n[{i}] {ep.get('endpoint_name', 'بدون اسم')}")
                print(f"    🔗 الرابط: {ep.get('api_url', 'N/A')}")
                print(f"    🔑 المفتاح: {ep.get('api_key', 'N/A')}")
                print(f"    🆔 المعرف: {ep.get('endpoint_id', 'N/A')}")
            print(f"\n{'='*60}\n")

    elif args.command == "call":
        try:
            inputs = json.loads(args.input)
            result = call(args.endpoint_id, args.api_key, **inputs)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print("❌ خطأ: المدخلات يجب أن تكون JSON صالحاً", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ خطأ: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
