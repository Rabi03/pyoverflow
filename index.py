from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import fire
import sys
import re
import requests
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE
from PyQt5.QtWebEngineWidgets import *
import json


def execute_command(command):
    process = Popen(
        command,
        stdout=PIPE,
        stderr=PIPE,
        cwd=None,
        shell=False,
        close_fds=True,
    )
    output, error = [], []

    for line in iter(process.stdout.readline, b''):
        output.append(line.decode("utf-8"))
    process.stdout.close()

    for line in iter(process.stderr.readline, b''):
        error.append(line.decode("utf-8"))
    process.stderr.close()

    output = ' '.join(output)
    error = ' '.join(error)

    return (output, error)


def get_language(file):
    if file.endswith('py'):
        return 'python'
    elif file.endswith('js'):
        return 'node'
    elif file.endswith('java'):
        return 'javac'
    elif file.endswith('class'):
        return "java"
    else:
        return ""
# python index.py exam.js


def get_error_message(error, language):
    if error == '':
        return None
    elif language == 'python':
        if any(e in error for e in ["KeyboardInterrupt", "SystemExit", "GeneratorExit"]):
            return None
        else:
            return error.split('\n')[-2].strip()

    elif language == 'node':
        return error.split('\n')[4][1:]


def get_stackoverflow_results(query):
    response = requests.get(
        f'https://api.stackexchange.com/2.3/search/advanced?pagesize=50&page=1&q={query}&order=desc&sort=votes&site=stackoverflow')

    result = json.loads(response.text)
    return result['items']


def open_app(gui, results):

    confirm = QMessageBox.question(
        gui.w, 'PyOverflow', "Are you sure to see the results?", QMessageBox.Yes | QMessageBox.No)
    if confirm == QMessageBox.Yes:
        layout = QGridLayout()

        gui.w.setLayout(layout)
        tab = QTabWidget()
        tab.findChild(QTabBar).hide()
        listwidget = QListWidget()
        for item in results:
            question = QListWidgetItem("👨‍💻 "+item['title'])
            question.setData(Qt.UserRole, [tab, listwidget, int(
                item.get("accepted_answer_id", 0))])
            listwidget.addItem(question)
            label = QListWidgetItem(listwidget)
            label.setText(
                f'Answers {item["answer_count"]} 🔹 views{item["view_count"]}')
            label.setFont(QFont("Roboto", 9))

            listwidget.addItem(label)
        listwidget.itemClicked.connect(open_answer_page)

        listwidget.setFont(QFont("Roboto", 16))
        listwidget.setSpacing(4)

        tab.insertTab(0, listwidget, "Search")

        layout.addWidget(tab)

        gui.w.show()


def open_answer_page(item):
    answerId = item.data(Qt.UserRole)[2]
    tab = item.data(Qt.UserRole)[0]
    prev_widget = item.data(Qt.UserRole)[1]
    widget = QWidget()
    newLayout = QGridLayout()
    text = QTextEdit(widget)

    navtb = QToolBar("Navigation")
    back_btn = QAction("⬅️", widget)
    back_btn.setFont(QFont("Roboto", 16))
    navtb.addAction(back_btn)

    back_btn.triggered.connect(lambda: tab.setCurrentIndex(0))
    if answerId > 0:
        html = requests.get(f'https://stackoverflow.com/questions/{answerId}')
        soup = BeautifulSoup(html.text, 'lxml')
        header = soup.find('div', id="question-header")
        head = QTextEdit(f'<h2>{header.h1.text}</h2>')
        head.setMaximumHeight(50)
        navtb.addWidget(head)

        answers = soup.find_all('div', class_="answercell post-layout--right")
        ansHtml = ""
        for ans in answers:
            res = ans.find('div', class_="s-prose js-post-body")
            ansHtml += "<p>Answer:</p>"+str(res)+"<br/><hr/>"
        text.append(ansHtml)

        text.setReadOnly(True)
        text.setFont(QFont("Roboto", 16))
        c = text.textCursor()
        c.movePosition(QTextCursor.Start)
        text.setTextCursor(c)
        newLayout.addWidget(navtb)
        newLayout.addWidget(text)
        newLayout.setSpacing(2)
        widget.setLayout(newLayout)

        tab.insertTab(1, widget, "Result")
        tab.setCurrentIndex(1)

    # browser = QWebEngineView()
    # browser.setUrl(QUrl("http://google.com"))


def go_back(layout, prev_widget, widget):
    layout.removeWidget(widget)
    layout.addWidget(prev_widget)


class Gui:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.w = QWidget()


def runFile(fileName=None):
    gui = Gui()
    gui.w.resize(1000, 800)
    if fileName == None:
        name, done = QInputDialog.getText(
            gui.w, 'Input Dialog', 'Enter file name:')
        if done:
            fileName = name
        else:
            return

        gui.w.show()
        gui.w.close()
    (output, error) = execute_command(f'node {fileName}')
    if (output, error) == (None, None):
        return
    else:
        language = get_language(fileName)
        getErrorMessage = get_error_message(error, language)

        query = f'{language} {getErrorMessage}'
        res = get_stackoverflow_results(query.replace(' ', '+'))
        if len(res) > 0:
            open_app(gui, res)

    sys.exit(gui.app.exec_())


if __name__ == "__main__":

    fire.Fire(runFile)
