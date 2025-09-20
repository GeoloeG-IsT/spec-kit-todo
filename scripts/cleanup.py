#!/usr/bin/env python3
"""
Code cleanup script for TODO application
Removes unused imports, fixes formatting, and optimizes code
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, cwd: str = None) -> bool:
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(
            cmd.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {cmd}: {e.stderr}")
        return False


def cleanup_backend():
    """Clean up backend code"""
    backend_dir = Path("backend")

    print("🧹 Cleaning up backend code...")

    # Sort imports with isort
    print("  📋 Sorting imports with isort...")
    run_command("isort src/ tests/", cwd=str(backend_dir))

    # Format with black
    print("  🎨 Formatting code with black...")
    run_command("black src/ tests/", cwd=str(backend_dir))

    # Remove unused imports with autoflake
    print("  🗑️  Removing unused imports...")
    run_command(
        "autoflake --remove-all-unused-imports --remove-unused-variables "
        "--in-place --recursive src/ tests/",
        cwd=str(backend_dir)
    )

    # Check with flake8
    print("  ✅ Checking code style with flake8...")
    run_command("flake8 src/ tests/", cwd=str(backend_dir))

    print("✅ Backend cleanup complete!")


def cleanup_frontend():
    """Clean up frontend code"""
    frontend_dir = Path("frontend")

    print("🧹 Cleaning up frontend code...")

    # Format with prettier
    print("  🎨 Formatting code with prettier...")
    run_command("npm run format", cwd=str(frontend_dir))

    # Lint with ESLint
    print("  ✅ Linting code with ESLint...")
    run_command("npm run lint -- --fix", cwd=str(frontend_dir))

    # Type check
    print("  🔍 Type checking with TypeScript...")
    run_command("npm run type-check", cwd=str(frontend_dir))

    print("✅ Frontend cleanup complete!")


def remove_unused_files():
    """Remove unused files and directories"""
    print("🗑️  Removing unused files...")

    # Common patterns to clean up
    patterns_to_remove = [
        "**/.DS_Store",
        "**/*.pyc",
        "**/__pycache__",
        "**/node_modules/.cache",
        "**/.pytest_cache",
        "**/coverage",
        "**/.nyc_output",
        "**/dist",
        "**/.next",
        "**/out",
    ]

    for pattern in patterns_to_remove:
        for path in Path(".").rglob(pattern):
            if path.exists():
                if path.is_file():
                    path.unlink()
                    print(f"  Removed file: {path}")
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                    print(f"  Removed directory: {path}")


def optimize_docker_files():
    """Optimize Docker files"""
    print("🐳 Optimizing Docker files...")

    # Check if .dockerignore files exist and are comprehensive
    dockerignore_paths = [
        Path("backend/.dockerignore"),
        Path("frontend/.dockerignore"),
    ]

    for dockerignore_path in dockerignore_paths:
        if dockerignore_path.exists():
            with open(dockerignore_path, 'r') as f:
                content = f.read()

            # Add common ignore patterns if missing
            patterns_to_add = [
                "node_modules",
                ".git",
                ".gitignore",
                "README.md",
                "*.md",
                ".env*",
                "coverage",
                "dist",
                ".nyc_output",
                "__pycache__",
                "*.pyc",
                ".pytest_cache",
                "tests",
            ]

            missing_patterns = []
            for pattern in patterns_to_add:
                if pattern not in content:
                    missing_patterns.append(pattern)

            if missing_patterns:
                with open(dockerignore_path, 'a') as f:
                    f.write("\n# Added by cleanup script\n")
                    for pattern in missing_patterns:
                        f.write(f"{pattern}\n")
                print(f"  Updated {dockerignore_path}")


def update_gitignore():
    """Update .gitignore with comprehensive patterns"""
    print("📝 Updating .gitignore...")

    gitignore_path = Path(".gitignore")

    additional_patterns = [
        "\n# IDE and editor files",
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",

        "\n# OS files",
        ".DS_Store",
        "Thumbs.db",

        "\n# Test coverage",
        "coverage/",
        ".nyc_output/",
        "htmlcov/",
        ".coverage",
        "coverage.xml",

        "\n# Temporary files",
        "*.tmp",
        "*.temp",
        "*.log",

        "\n# Build artifacts",
        "dist/",
        "build/",
        "*.egg-info/",

        "\n# Deployment",
        ".env.production",
        ".env.staging",
    ]

    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            current_content = f.read()

        patterns_to_add = []
        for pattern in additional_patterns:
            if pattern.strip() and pattern.strip() not in current_content:
                patterns_to_add.append(pattern)

        if patterns_to_add:
            with open(gitignore_path, 'a') as f:
                f.write("\n# Added by cleanup script")
                for pattern in patterns_to_add:
                    f.write(f"{pattern}\n")
            print("  Updated .gitignore")


def main():
    """Main cleanup function"""
    print("🚀 Starting code cleanup...")

    # Change to project root
    os.chdir(Path(__file__).parent.parent)

    try:
        # Clean up backend
        if Path("backend").exists():
            cleanup_backend()

        # Clean up frontend
        if Path("frontend").exists():
            cleanup_frontend()

        # Remove unused files
        remove_unused_files()

        # Optimize Docker files
        optimize_docker_files()

        # Update gitignore
        update_gitignore()

        print("\n🎉 Code cleanup completed successfully!")
        print("\nNext steps:")
        print("1. Review the changes with: git diff")
        print("2. Run tests to ensure everything works: npm test && pytest")
        print("3. Commit the cleanup: git add . && git commit -m 'Code cleanup and optimization'")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()