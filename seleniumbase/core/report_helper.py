import os
import shutil
import sys
import time
from selenium import webdriver
from seleniumbase.config import settings
from seleniumbase.core.style_sheet import style
from seleniumbase.fixtures import page_actions

LATEST_REPORT_DIR = settings.LATEST_REPORT_DIR
ARCHIVE_DIR = settings.REPORT_ARCHIVE_DIR
HTML_REPORT = settings.HTML_REPORT
RESULTS_TABLE = settings.RESULTS_TABLE


def get_timestamp():
    return str(int(time.time() * 1000))


def process_successes(test, test_count):
    return(
        '"%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            test_count,
            "Passed!",
            "*",
            "*",
            "*",
            test.browser,
            get_timestamp()[:-3],
            test.id(),
            "*"))


def process_failures(test, test_count, browser_type):
    bad_page_image = "failure_%s.jpg" % test_count
    bad_page_data = "failure_%s.txt" % test_count
    page_actions.save_screenshot(
        test.driver, bad_page_image, folder=LATEST_REPORT_DIR)
    page_actions.save_test_failure_data(
        test.driver, bad_page_data, browser_type, folder=LATEST_REPORT_DIR)
    exc_info = '(Unknown Failure)'
    exception = sys.exc_info()[1]
    if exception:
        if hasattr(exception, 'msg'):
            exc_info = exception.msg
        elif hasattr(exception, 'message'):
            exc_info = exception.message
        else:
            pass
    return(
        '"%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
            test_count,
            "FAILED!",
            bad_page_data,
            bad_page_image,
            test.driver.current_url,
            test.browser,
            get_timestamp()[:-3],
            test.id(),
            exc_info))


def clear_out_old_report_logs(archive_past_runs=True, get_log_folder=False):
        abs_path = os.path.abspath('.')
        file_path = abs_path + "/%s" % LATEST_REPORT_DIR
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        if archive_past_runs:
            archive_timestamp = int(time.time())
            if not os.path.exists("%s/../%s/" % (file_path, ARCHIVE_DIR)):
                os.makedirs("%s/../%s/" % (file_path, ARCHIVE_DIR))
            archive_dir = "%s/../%s/report_%s" % (
                file_path, ARCHIVE_DIR, archive_timestamp)
            shutil.move(file_path, archive_dir)
            os.makedirs(file_path)
            if get_log_folder:
                return archive_dir
        else:
            # Just delete bad pages to make room for the latest run.
            filelist = [f for f in os.listdir(
                "./%s" % LATEST_REPORT_DIR) if f.startswith("failure_") or (
                f == HTML_REPORT) or (f.startswith("automation_failure")) or (
                f == RESULTS_TABLE)]
            for f in filelist:
                os.remove("%s/%s" % (file_path, f))


def add_bad_page_log_file(page_results_list):
    abs_path = os.path.abspath('.')
    file_path = abs_path + "/%s" % LATEST_REPORT_DIR
    log_file = "%s/%s" % (file_path, RESULTS_TABLE)
    f = open(log_file, 'w')
    h_p1 = '''"Num","Result","Failure Info","Screenshot",'''
    h_p2 = '''"URL","Browser","Epoch Time",'''
    h_p3 = '''"Test Case Address","Additional Info"\n'''
    page_header = h_p1 + h_p2 + h_p3
    f.write(page_header)
    for line in page_results_list:
        f.write("%s\n" % line)
    f.close()


def archive_new_report_logs():
    log_string = clear_out_old_report_logs(get_log_folder=True)
    log_folder = log_string.split('/')[-1]
    abs_path = os.path.abspath('.')
    file_path = abs_path + "/%s" % ARCHIVE_DIR
    report_log_path = "%s/%s" % (file_path, log_folder)
    return report_log_path


def add_results_page(html):
    abs_path = os.path.abspath('.')
    file_path = abs_path + "/%s" % LATEST_REPORT_DIR
    results_file_name = HTML_REPORT
    results_file = "%s/%s" % (file_path, results_file_name)
    f = open(results_file, 'w')
    f.write(html)
    f.close()
    return results_file


def build_report(report_log_path, page_results_list,
                 successes, failures, browser_type,
                 hide_report):

    web_log_path = "file://%s" % report_log_path
    successes_count = len(successes)
    failures_count = len(failures)
    total_test_count = successes_count + failures_count

    tf_color = "#11BB11"
    if failures_count > 0:
        tf_color = "#EE3A3A"

    summary_table = '''<div><table><thead><tr>
        <th>TEST REPORT SUMMARY</th>
        <th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
        </tr></thead><tbody>
        <tr style="color:#00BB00"><td>TESTS PASSING: <td>%s</tr>
        <tr style="color:%s"     ><td>TESTS FAILING: <td>%s</tr>
        <tr style="color:#4D4DDD"><td>TOTAL TESTS: <td>%s</tr>
        </tbody></table>''' % (successes_count,
                               tf_color,
                               failures_count,
                               total_test_count)

    summary_table = '''<h1 id="ContextHeader" class="sectionHeader" title="">
        %s</h1>''' % summary_table

    log_link_shown = '../%s%s/' % (
        ARCHIVE_DIR, web_log_path.split(ARCHIVE_DIR)[1])
    csv_link = '%s/%s' % (web_log_path, RESULTS_TABLE)
    csv_link_shown = '%s' % RESULTS_TABLE
    log_table = '''<p><p><p><p><h2><table><tbody>
        <tr><td>LOG FILES LINK:&nbsp;&nbsp;<td><a href="%s">%s</a></tr>
        <tr><td>RESULTS TABLE:&nbsp;&nbsp;<td><a href="%s">%s</a></tr>
        </tbody></table></h2><p><p><p><p>''' % (
        web_log_path, log_link_shown, csv_link, csv_link_shown)

    failure_table = '<h2><table><tbody></div>'
    any_screenshots = False
    for line in page_results_list:
        line = line.split(',')
        if line[1] == '"FAILED!"':
            if not any_screenshots:
                any_screenshots = True
                failure_table += '''<thead><tr>
                    <th>STACKTRACE&nbsp;&nbsp;</th>
                    <th>SCREENSHOT&nbsp;&nbsp;</th>
                    <th>LOCATION OF FAILURE</th>
                    </tr></thead>'''
            display_url = line[4]
            if len(display_url) > 60:
                display_url = display_url[0:58] + '...'
            line = '<a href="%s">%s</a>' % (
                "file://" + report_log_path + '/' + line[2], line[2]) + '''
                &nbsp;&nbsp;
                ''' + '<td><a href="%s">%s</a>' % (
                "file://" + report_log_path + '/' + line[3], line[3]) + '''
                &nbsp;&nbsp;
                ''' + '<td><a href="%s">%s</a>' % (line[4], display_url)
            line = line.replace('"', '')
            failure_table += '<tr><td>%s</tr>\n' % line
    failure_table += '</tbody></table></h2>'

    failing_list = ''
    if failures:
        failing_list = '<h2><table><tbody>'
        failing_list += '''<thead><tr><th>LIST OF FAILING TESTS
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                        </th></tr></thead>'''
        for failure in failures:
            failing_list += '<tr style="color:#EE3A3A"><td>%s</tr>\n' % failure
        failing_list += '</tbody></table></h2>'

    passing_list = ''
    if successes:
        passing_list = '<h2><table><tbody>'
        passing_list += '''<thead><tr><th>LIST OF PASSING TESTS
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                        </th></tr></thead>'''
        for success in successes:
            passing_list += '<tr style="color:#00BB00"><td>%s</tr>\n' % success
        passing_list += '</tbody></table></h2>'

    table_view = '%s%s%s%s%s' % (
        summary_table, log_table, failure_table, failing_list, passing_list)
    report_html = '<html><head>%s</head><body>%s</body></html>' % (
        style, table_view)
    results_file = add_results_page(report_html)
    archived_results_file = report_log_path + '/' + HTML_REPORT
    shutil.copyfile(results_file, archived_results_file)
    print "\n* The latest html report page is located at:\n" + results_file
    print "\n* Files saved for this report are located at:\n" + report_log_path
    print ""
    if not hide_report:
        if browser_type == 'chrome':
            browser = webdriver.Chrome()
        else:
            browser = webdriver.Firefox()
        browser.get("file://%s" % archived_results_file)
        print "\n*** Close the html report window to continue. ***"
        while len(browser.window_handles):
            time.sleep(0.1)
        browser.quit()
