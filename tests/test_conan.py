import asyncio
import os
import sys
from unittest.mock import Mock, patch

try:
    from unittest.mock import AsyncMock
except ImportError:
    ...  # skip tests for Python < 3.8

import pytest

from conan_check_updates.conan import (
    ConanError,
    ConanReference,
    find_conan,
    find_conanfile,
    run_info,
    run_search,
)
from conan_check_updates.version import Version

asyncmock_required = pytest.mark.skipif(
    sys.version_info < (3, 8),
    reason="Python 3.8 required for AsyncMock mocking",
)


def test_find_conan():
    find_conan.cache_clear()
    result = find_conan()
    assert result.path
    assert result.path.stem.lower() == "conan"
    assert result.version
    assert result.version.major in (1, 2)


@patch.dict(os.environ, {"PATH": ""})
def test_find_conan_fail():
    find_conan.cache_clear()
    with pytest.raises(RuntimeError, match="Conan executable not found"):
        find_conan()


@pytest.mark.parametrize("conanfile", ["conanfile.py", "conanfile.txt"])
def test_find_conanfile(tmp_path, conanfile):
    conanfile_path = tmp_path / conanfile

    with pytest.raises(ValueError, match="Could not find conanfile in path"):
        find_conanfile(tmp_path)
    with pytest.raises(ValueError, match="Invalid path"):
        find_conanfile(conanfile_path)

    conanfile_path.touch()  # create conanfile

    result_path = find_conanfile(tmp_path)
    result_file = find_conanfile(conanfile_path)

    assert result_path.name == conanfile
    assert result_path.name == conanfile
    assert result_path == result_file


@pytest.mark.parametrize(
    ("reference", "package", "version", "user", "channel"),
    [
        ("pkg/0.1.0", "pkg", Version("0.1.0"), None, None),
        ("pkg/0.1.0@user/stable", "pkg", Version("0.1.0"), "user", "stable"),
    ],
)
def test_parse_conan_reference(reference, package, version, user, channel):
    result = ConanReference(reference)
    assert result.package == package
    assert result.version == version
    assert result.user == user
    assert result.channel == channel


@pytest.mark.parametrize(
    "invalid_reference",
    ["x", "x/1.0.0", "xyz/1.0.0@user", "xyz/1.0.0@a/b"],
)
def test_validate_conan_reference(invalid_reference):
    with pytest.raises(ValueError, match="Invalid Conan reference"):
        ConanReference(invalid_reference)


@pytest.fixture(name="mock_process")
def fixture_mock_process():
    with patch("asyncio.create_subprocess_shell") as mock:
        process = Mock(spec=asyncio.subprocess.Process)  # pylint: disable=no-member
        mock.return_value = process
        yield process


CONAN_V1_INFO_STDOUT = b"""
Version ranges solved
    Version range '>=2.10.0' required by 'conanfile.txt' resolved to 'catch2/2.13.7' in local cache
    Version range '>=3.20' required by 'conanfile.txt' resolved to 'cmake/3.22.0' in local cache

[{"reference": "conanfile.txt", "is_ref": false, "display_name": "conanfile.txt", "id": "c5cf74a5adb1e1f5ef7a73610a06eda03c72151c", "build_id": null, "context": "host", "requires": ["catch2/2.13.7", "fmt/8.0.0", "spdlog/1.9.0", "nlohmann_json/3.7.3"], "build_requires": ["cmake/3.22.0"]}, {"revision": "0", "reference": "catch2/2.13.7", "is_ref": true, "display_name": "catch2/2.13.7", "id": "5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9", "build_id": null, "context": "host", "remote": {"name": "conancenter", "url": "https://center.conan.io"}, "url": "https://github.com/conan-io/conan-center-index", "homepage": "https://github.com/catchorg/Catch2", "license": ["BSL-1.0"], "description": "A modern, C++-native, header-only, framework for unit-tests, TDD and BDD", "topics": ["conan", "catch2", "header-only", "unit-test", "tdd", "bdd"], "provides": ["catch2"], "recipe": "Cache", "package_revision": "0", "binary": "Download", "binary_remote": "conancenter", "creation_date": "2021-11-05 20:54:20 UTC", "required_by": ["conanfile.txt"]}, {"revision": "0", "reference": "cmake/3.22.0", "is_ref": true, "display_name": "cmake/3.22.0", "id": "0a420ff5c47119e668867cdb51baff0eca1fdb68", "build_id": null, "context": "host", "remote": {"name": "conancenter", "url": "https://center.conan.io"}, "url": "https://github.com/conan-io/conan-center-index", "homepage": "https://github.com/Kitware/CMake", "license": ["BSD-3-Clause"], "description": "Conan installer for CMake", "topics": ["cmake", "build", "installer"], "provides": ["cmake"], "recipe": "Cache", "package_revision": "0", "binary": "Download", "binary_remote": "conancenter", "creation_date": "2021-11-19 05:18:58 UTC", "required_by": ["conanfile.txt"]}, {"revision": "0", "reference": "fmt/8.0.0", "is_ref": true, "display_name": "fmt/8.0.0", "id": "2be90237c5e294c2f30bf6b043d047624b893db3", "build_id": null, "context": "host", "remote": {"name": "conancenter", "url": "https://center.conan.io"}, "url": "https://github.com/conan-io/conan-center-index", "homepage": "https://github.com/fmtlib/fmt", "license": ["MIT"], "description": "A safe and fast alternative to printf and IOStreams.", "topics": ["conan", "fmt", "format", "iostream", "printf"], "provides": ["fmt"], "recipe": "Cache", "package_revision": "0", "binary": "Download", "binary_remote": "conancenter", "creation_date": "2021-10-15 17:59:52 UTC", "required_by": ["spdlog/1.9.0", "conanfile.txt"]}, {"revision": "0", "reference": "nlohmann_json/3.7.3", "is_ref": true, "display_name": "nlohmann_json/3.7.3", "id": "5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9", "build_id": null, "context": "host", "remote": {"name": "conancenter", "url": "https://center.conan.io"}, "url": "https://github.com/conan-io/conan-center-index", "homepage": "https://github.com/nlohmann/json", "license": ["MIT"], "description": "JSON for Modern C++ parser and generator.", "topics": ["conan", "jsonformoderncpp", "nlohmann_json", "json", "header-only"], "provides": ["nlohmann_json"], "recipe": "Cache", "package_revision": "0", "binary": "Download", "binary_remote": "conancenter", "creation_date": "2021-08-01 11:51:22 UTC", "required_by": ["conanfile.txt"]}, {"revision": "0", "reference": "spdlog/1.9.0", "is_ref": true, "display_name": "spdlog/1.9.0", "id": "26b885d7ef0883598f1d5dc9d2e504e10115011f", "build_id": null, "context": "host", "remote": {"name": "conancenter", "url": "https://center.conan.io"}, "url": "https://github.com/conan-io/conan-center-index", "homepage": "https://github.com/gabime/spdlog", "license": ["MIT"], "description": "Fast C++ logging library", "topics": ["conan", "spdlog", "logging", "header-only"], "provides": ["spdlog"], "recipe": "Cache", "package_revision": "0", "binary": "Download", "binary_remote": "conancenter", "creation_date": "2021-07-29 19:55:23 UTC", "required_by": ["conanfile.txt"], "requires": ["fmt/8.0.0"]}]
""".lstrip()  # noqa: E501


@asyncmock_required
@pytest.mark.asyncio()
async def test_run_info(mock_process):
    stdout = CONAN_V1_INFO_STDOUT
    stderr = b""
    mock_process.communicate = AsyncMock(return_value=(stdout, stderr))
    mock_process.returncode = 0

    result = await run_info(".")
    assert result.reference == "conanfile.txt"
    assert result.requires == [
        "catch2/2.13.7",
        "fmt/8.0.0",
        "spdlog/1.9.0",
        "nlohmann_json/3.7.3",
    ]
    assert result.build_requires == [
        "cmake/3.22.0",
    ]


# Conan v1: conan search --remote all --raw fmt
CONAN_V1_SEARCH_STDOUT = b"""
Remote 'conancenter':
fmt/5.3.0
fmt/6.0.0
fmt/6.1.0
""".lstrip()

# Conan v2: conan search fmt
CONAN_V2_SEARCH_STDOUT = b"""
conancenter:
  fmt
    fmt/5.3.0
    fmt/6.0.0
    fmt/6.1.0
""".lstrip()


@asyncmock_required
@pytest.mark.asyncio()
@pytest.mark.parametrize(
    "response",
    [CONAN_V1_SEARCH_STDOUT, CONAN_V2_SEARCH_STDOUT],
    ids=["Conan v1", "Conan v2"],
)
async def test_run_search(mock_process, response):
    stdout = response
    stderr = b""
    mock_process.communicate = AsyncMock(return_value=(stdout, stderr))
    mock_process.returncode = 0

    refs = await run_search("fmt")

    assert len(refs) == 3
    assert refs[0] == ConanReference("fmt/5.3.0")
    assert refs[1] == ConanReference("fmt/6.0.0")
    assert refs[2] == ConanReference("fmt/6.1.0")


@asyncmock_required
@pytest.mark.asyncio()
async def test_run_search_no_results(mock_process):
    mock_process.communicate = AsyncMock(return_value=(b"", b""))
    mock_process.returncode = 0

    refs = await run_search("")
    assert len(refs) == 0


@asyncmock_required
@pytest.mark.asyncio()
async def test_run_search_fail(mock_process):
    mock_process.communicate = AsyncMock(return_value=(b"", b"Error..."))
    mock_process.returncode = 1

    with pytest.raises(ConanError, match="Error..."):
        await run_search("")
