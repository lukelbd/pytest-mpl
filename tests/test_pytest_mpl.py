import os
import sys
import json
import subprocess
from pathlib import Path

import matplotlib
import matplotlib.ft2font
import matplotlib.pyplot as plt
import pytest
from packaging.version import Version

MPL_VERSION = Version(matplotlib.__version__)

baseline_dir = 'baseline'

if MPL_VERSION >= Version('2'):
    baseline_subdir = '2.0.x'

baseline_dir_local = os.path.join(baseline_dir, baseline_subdir)
baseline_dir_remote = 'http://matplotlib.github.io/pytest-mpl/' + baseline_subdir + '/'

ftv = matplotlib.ft2font.__freetype_version__.replace('.', '')
hash_filename = f"mpl{MPL_VERSION.major}{MPL_VERSION.minor}_ft{ftv}.json"

if "+" in matplotlib.__version__:
    hash_filename = "mpldev.json"

hash_library = (Path(__file__).parent / "baseline" /  # noqa
                "hashes" / hash_filename)

fail_hash_library = Path(__file__).parent / "baseline" / "test_hash_lib.json"
baseline_dir_abs = Path(__file__).parent / "baseline" / baseline_subdir
hash_baseline_dir_abs = Path(__file__).parent / "baseline" / "hybrid"


WIN = sys.platform.startswith('win')

# In some cases, the fonts on Windows can be quite different
DEFAULT_TOLERANCE = 10 if WIN else 2


def call_pytest(args):
    return subprocess.call([sys.executable, '-m', 'pytest', '-s'] + args)


def assert_pytest_fails_with(args, output_substring):
    try:
        subprocess.check_output([sys.executable, '-m', 'pytest', '-s'] + args)
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        assert output_substring in output, output
        return output
    else:
        raise RuntimeError(f'pytest did not fail with args {args}')


@pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_local,
                               tolerance=DEFAULT_TOLERANCE)
def test_succeeds():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3])
    return fig


@pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_remote,
                               tolerance=DEFAULT_TOLERANCE)
def test_succeeds_remote():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3])
    return fig


# The following tries an invalid URL first (or at least a URL where the baseline
# image won't exist), but should succeed with the second mirror.
@pytest.mark.mpl_image_compare(baseline_dir='http://www.python.org,' + baseline_dir_remote,
                               filename='test_succeeds_remote.png',
                               tolerance=DEFAULT_TOLERANCE)
def test_succeeds_faulty_mirror():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3])
    return fig


class TestClass(object):

    @pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_local,
                                   tolerance=DEFAULT_TOLERANCE)
    def test_succeeds(self):
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot([1, 2, 3])
        return fig


@pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_local,
                               savefig_kwargs={'dpi': 30},
                               tolerance=DEFAULT_TOLERANCE)
def test_dpi():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3])
    return fig


TEST_FAILING = """
import pytest
import matplotlib.pyplot as plt
@pytest.mark.mpl_image_compare
def test_fail():
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,2])
    return fig
"""


def test_fails(tmpdir):

    test_file = tmpdir.join('test.py').strpath
    with open(test_file, 'w') as f:
        f.write(TEST_FAILING)

    # If we use --mpl, it should detect that the figure is wrong
    code = call_pytest(['--mpl', test_file])
    assert code != 0

    # If we don't use --mpl option, the test should succeed
    code = call_pytest([test_file])
    assert code == 0


TEST_OUTPUT_DIR = """
import pytest
import matplotlib.pyplot as plt
@pytest.mark.mpl_image_compare
def test_output_dir():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3])
    return fig
"""


def test_output_dir(tmpdir):
    test_file = tmpdir.join('test.py').strpath
    with open(test_file, 'w') as f:
        f.write(TEST_OUTPUT_DIR)

    output_dir = tmpdir.join('test_output_dir')

    # When we run the test, we should get output images where we specify
    code = call_pytest([f'--mpl-results-path={output_dir}',
                        '--mpl', test_file])

    assert code != 0
    assert output_dir.exists()
    assert (output_dir / "test.test_output_dir" / "result.png").exists()


TEST_GENERATE = """
import pytest
import matplotlib.pyplot as plt
@pytest.mark.mpl_image_compare
def test_gen():
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,3])
    return fig
"""


def test_generate(tmpdir):

    test_file = tmpdir.join('test.py').strpath
    with open(test_file, 'w') as f:
        f.write(TEST_GENERATE)

    gen_dir = tmpdir.mkdir('spam').mkdir('egg').strpath

    # If we don't generate, the test will fail
    assert_pytest_fails_with(['--mpl', test_file], 'Image file not found for comparison test')

    # If we do generate, the test should succeed and a new file will appear
    code = call_pytest([f'--mpl-generate-path={gen_dir}', test_file])
    assert code == 0
    assert os.path.exists(os.path.join(gen_dir, 'test_gen.png'))

    # If we do generate hash, the test will fail as no image is present
    hash_file = os.path.join(gen_dir, 'test_hashes.json')
    code = call_pytest([f'--mpl-generate-hash-library={hash_file}', test_file])
    assert code == 1
    assert os.path.exists(hash_file)

    with open(hash_file) as fp:
        hash_lib = json.load(fp)

    assert "test.test_gen" in hash_lib


@pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_local, tolerance=20)
def test_tolerance():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 2])
    return fig


def test_nofigure():
    pass


@pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_local,
                               style='fivethirtyeight',
                               tolerance=DEFAULT_TOLERANCE)
def test_base_style():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3])
    return fig


@pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_local,
                               remove_text=True)
def test_remove_text():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3])
    return fig


@pytest.mark.parametrize('s', [5, 50, 500])
@pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_local,
                               remove_text=True)
def test_parametrized(s):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter([1, 3, 4, 3, 2], [1, 4, 3, 3, 1], s=s)
    return fig


class TestClassWithSetup:

    # Regression test for a bug that occurred when using setup_method

    def setup_method(self, method):
        self.x = [1, 2, 3]

    @pytest.mark.mpl_image_compare(baseline_dir=baseline_dir_local,
                                   filename='test_succeeds.png',
                                   tolerance=DEFAULT_TOLERANCE)
    def test_succeeds(self):
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(self.x)
        return fig


# hashlib

@pytest.mark.skipif(not hash_library.exists(), reason="No hash library for this mpl version")
@pytest.mark.mpl_image_compare(hash_library=hash_library)
def test_hash_succeeds():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3])
    return fig


TEST_FAILING_HASH = rf"""
import pytest
import matplotlib.pyplot as plt
@pytest.mark.mpl_image_compare(hash_library=r"{fail_hash_library}")
def test_hash_fails():
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,2])
    return fig
"""


def test_hash_fails(tmpdir):

    test_file = tmpdir.join('test.py').strpath
    with open(test_file, 'w', encoding='ascii') as f:
        f.write(TEST_FAILING_HASH)

    # If we use --mpl, it should detect that the figure is wrong
    output = assert_pytest_fails_with(['--mpl', test_file], "doesn't match hash FAIL in library")
    # We didn't specify a baseline dir so we shouldn't attempt to find one
    assert "Unable to find baseline image" not in output, output

    # Check that the summary path is printed and that it exists.
    output = assert_pytest_fails_with(['--mpl', test_file, '--mpl-generate-summary=html'],
                                      "doesn't match hash FAIL in library")
    # We didn't specify a baseline dir so we shouldn't attempt to find one
    print_message = "A summary of the failed tests can be found at:"
    assert print_message in output, output
    printed_path = Path(output.split(print_message)[1].strip())
    assert printed_path.exists()

    # If we don't use --mpl option, the test should succeed
    code = call_pytest([test_file])
    assert code == 0


TEST_FAILING_HYBRID = rf"""
import pytest
import matplotlib.pyplot as plt
@pytest.mark.mpl_image_compare(hash_library=r"{fail_hash_library}",
                               tolerance=2)
def test_hash_fail_hybrid():
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,3])
    return fig
"""


@pytest.mark.skipif(ftv != '261', reason="Incorrect freetype version for hash check")
def test_hash_fail_hybrid(tmpdir):

    test_file = tmpdir.join('test.py').strpath
    with open(test_file, 'w', encoding='ascii') as f:
        f.write(TEST_FAILING_HYBRID)

    # Assert that image comparison runs and fails
    output = assert_pytest_fails_with(['--mpl', test_file,
                                       rf'--mpl-baseline-path={hash_baseline_dir_abs / "fail"}'],
                                      "doesn't match hash FAIL in library")
    assert "Error: Image files did not match." in output, output

    # Assert reports missing baseline image
    output = assert_pytest_fails_with(['--mpl', test_file,
                                       '--mpl-baseline-path=/not/a/path'],
                                      "doesn't match hash FAIL in library")
    assert "Unable to find baseline image" in output, output

    # Assert reports image comparison succeeds
    output = assert_pytest_fails_with(['--mpl', test_file,
                                       rf'--mpl-baseline-path={hash_baseline_dir_abs / "succeed"}'],
                                      "doesn't match hash FAIL in library")
    assert "However, the comparison to the baseline image succeeded." in output, output

    # If we don't use --mpl option, the test should succeed
    code = call_pytest([test_file])
    assert code == 0


TEST_FAILING_NEW_HASH = r"""
import pytest
import matplotlib.pyplot as plt
@pytest.mark.mpl_image_compare
def test_hash_fails():
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,2])
    return fig
"""


@pytest.mark.skipif(ftv != '261', reason="Incorrect freetype version for hash check")
def test_hash_fail_new_hashes(tmpdir):
    # Check that the hash comparison fails even if a new hash file is requested
    test_file = tmpdir.join('test.py').strpath
    with open(test_file, 'w', encoding='ascii') as f:
        f.write(TEST_FAILING_NEW_HASH)

    # Assert that image comparison runs and fails
    assert_pytest_fails_with(['--mpl', test_file,
                              f'--mpl-hash-library={fail_hash_library}'],
                             "doesn't match hash FAIL in library")

    hash_file = tmpdir.join('new_hashes.json').strpath
    # Assert that image comparison runs and fails
    assert_pytest_fails_with(['--mpl', test_file,
                              f'--mpl-hash-library={fail_hash_library}',
                              f'--mpl-generate-hash-library={hash_file}'],
                             "doesn't match hash FAIL")


TEST_MISSING_HASH = """
import pytest
import matplotlib.pyplot as plt
@pytest.mark.mpl_image_compare
def test_hash_missing():
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,2])
    return fig
"""


def test_hash_missing(tmpdir):

    test_file = tmpdir.join('test.py').strpath
    with open(test_file, 'w') as f:
        f.write(TEST_MISSING_HASH)

    # Assert fails if hash library missing
    assert_pytest_fails_with(['--mpl', test_file, '--mpl-hash-library=/not/a/path'],
                             "Can't find hash library at path")

    # Assert fails if hash not in library
    assert_pytest_fails_with(['--mpl', test_file, f'--mpl-hash-library={fail_hash_library}'],
                             "Hash for test 'test.test_hash_missing' not found in")

    # If we don't use --mpl option, the test should succeed
    code = call_pytest([test_file])
    assert code == 0


TEST_RESULTS_ALWAYS = """
import pytest
import matplotlib.pyplot as plt
def plot():
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,2])
    return fig
@pytest.mark.mpl_image_compare
def test_modified(): return plot()
@pytest.mark.mpl_image_compare
def test_new(): return plot()
@pytest.mark.mpl_image_compare
def test_unmodified(): return plot()
"""


@pytest.mark.skipif(not hash_library.exists(), reason="No hash library for this mpl version")
def test_results_always(tmpdir):

    test_file = tmpdir.join('test.py').strpath
    with open(test_file, 'w') as f:
        f.write(TEST_RESULTS_ALWAYS)
    results_path = tmpdir.mkdir('results')

    code = call_pytest(['--mpl', test_file, '--mpl-results-always',
                        rf'--mpl-hash-library={hash_library}',
                        rf'--mpl-baseline-path={baseline_dir_abs}',
                        '--mpl-generate-summary=html',
                        rf'--mpl-results-path={results_path.strpath}'])
    assert code == 0  # hashes correct, so all should pass

    comparison_file = results_path.join('fig_comparison.html')
    with open(comparison_file, 'r') as f:
        html = f.read()

    # each test, and which images should exist
    for test, exists in [
        ('test_modified', ['baseline', 'result-failed-diff', 'result']),
        ('test_new', ['result']),
        ('test_unmodified', ['baseline', 'result']),
    ]:

        test_name = f'test.{test}'

        summary = f'{test_name} (passed)'
        assert summary in html

        for image_type in ['baseline', 'result-failed-diff', 'result']:
            image = f'{test_name}/{image_type}.png'
            assert image in html  # <img> is present even if 404
            image_exists = results_path.join(*image.split('/')).exists()
            if image_type in exists:  # assert image so pytest prints it on error
                assert image and image_exists
            else:
                assert image and not image_exists
