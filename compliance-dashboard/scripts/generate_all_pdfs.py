"""
Generate All PDFs
Master script to generate all document types (NCR, Inspection, Maintenance)
"""
import subprocess
import sys
from pathlib import Path


def run_generator(script_name, doc_type):
    """Run a PDF generator script"""
    print(f"\n{'=' * 60}")
    print(f"Generating {doc_type} PDFs")
    print(f"{'=' * 60}\n")

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        print(f"\n✓ {doc_type} PDFs generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error generating {doc_type} PDFs: {e}")
        return False


def main():
    """Generate all PDF types"""
    scripts_dir = Path(__file__).parent

    print("=" * 60)
    print("Generate All Compliance PDFs")
    print("=" * 60)
    print("\nThis will generate:")
    print("  - 50 NCR Report PDFs")
    print("  - 20 Inspection Certificate PDFs")
    print("  - 15 Maintenance Work Order PDFs")
    print("\nTotal: 85 PDF documents\n")

    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        return

    generators = [
        (scripts_dir / 'generate_ncr_pdfs.py', 'NCR Reports'),
        (scripts_dir / 'generate_inspection_pdfs.py', 'Inspection Certificates'),
        (scripts_dir / 'generate_maintenance_pdfs.py', 'Maintenance Work Orders'),
    ]

    results = []
    for script, doc_type in generators:
        success = run_generator(script, doc_type)
        results.append((doc_type, success))

    # Summary
    print("\n" + "=" * 60)
    print("Generation Summary")
    print("=" * 60)

    for doc_type, success in results:
        status = "✓ Success" if success else "✗ Failed"
        print(f"{status}: {doc_type}")

    successful = sum(1 for _, success in results if success)
    print(f"\n{successful}/{len(results)} document types generated successfully")
    print("=" * 60)


if __name__ == '__main__':
    main()
