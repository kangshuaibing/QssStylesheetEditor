#!/usr/bin/env python3

__version__ = "1.0"

import sys
import os

from PyQt5.QtCore import (Qt, QEvent, QFile, QFileInfo, QIODevice, QRegExp, QTextStream,
                          pyqtSignal)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QFileDialog, QMessageBox,
                             QTextEdit)
from PyQt5.QtGui import (QFont, QKeyEvent,QColor)
from PyQt5.Qsci import *
from PyQt5 import Qsci

from .enums import BadEnum, EditorEnums
from .settings import *

sys.path.insert(0,os.path.join(os.path.dirname(__file__),"3rdparty.zip"))
import chardet

class CodeEditor(QsciScintilla):
    keyPress=pyqtSignal(QKeyEvent)
    loseFocus=pyqtSignal()
    mouseLeave=pyqtSignal()
    mousePress=pyqtSignal()

    def __init__(self, **config):
        super().__init__()
        self.coding="utf-8"
        self.settings={}
        self._set_default_config()
        # Override defaults with any customizations
        self.configure(**config)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPress.emit(event)

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self.loseFocus.emit()

    def leaveEvent(self, e):
        self.mouseLeave.emit()

    def mousePressEvent(self, QMouseEvent):
        super().mousePressEvent(QMouseEvent)
        self.mousePress.emit()

    def _set_default_config(self):
        """Set default configuration settings.
        """
        self.configure(
            # Fonts
            utf8 = True,  # 支持中文字符
            font = QFont('Consolas', 11),# 设置默认字体
            marginsFont = QFont('Courier New', 10),

            # Wrap mode: Wrap(None|Word|Character|Whitespace)
            wrapMode='WrapNone',  # self.setWrapMode(self.WrapWord)    # 自动换行
            # Text wrapping visual flag: WrapFlag(None|ByText|ByBorder|InMargin)
            wrapVisualFlags='WrapFlagNone',  # 无对应getter
            # End-of-line mode
            # EolMode: Eol(Windows|Unix|Mac) SC_EOL_CRLF|SC_EOL_LF|SC_EOL_CR
            # eolMode = self.SC_EOL_LF,# 以\n换行
            eolVisibility=False,  # 是否显示换行符

            # Whitespace: Ws(Invisible|Visible|VisibleAfterIndent)
            whitespaceVisibility='WsInvisible',#是否显示空格，类似word空格处显示为点
            #  WhitespaceSize: (0|1|2) 点大小，0不显示，1小点，2大点
            whitespaceSize=2,#

            # indent
            indentationsUseTabs = False,#False表示用空格代替\t
            tabWidth = 4,#空格数量，或者\t宽度
            indentationGuides = True,# 用tab键缩进时，在缩进位置上显示一个竖点线，缩进有效，在字符串后加空格不显示
            indentationWidth = 0,#如果在行首部空格位置tab，缩进的宽度字符数，并且不会转换为空格
            autoIndent = True,# 换行后自动缩进
            backspaceUnindents=True,
            tabIndents = True,#True如果行前空格数少于tabWidth，补齐空格数,False如果在文字前tab同true，如果在行首tab，则直接增加tabwidth个空格

            # current line color
            caretWidth=2,  # 光标宽度，0表示不显示光标
            caretForegroundColor=QColor("#ff000000"),#光标颜色
            caretLineVisible=True,#是否高亮显示光标所在行
            caretLineBackgroundColor=QColor('#FFF0F0F0'),#光标所在行背景颜色

            # selection color
            # selectionBackgroundColor=QColor("#606060"),
            # selectionForegroundColor=QColor("#FFFFFF"),

            # edges
            edgeColumn = 80,
            # Edge mode: Edge(None|Line|Background)
            edgeMode = 'EdgeLine',
            edgeColor = QColor('#FF88FFFF'),

            # Brace matching: (No|Strict|Sloppy)BraceMatch
            braceMatching='SloppyBraceMatch',

            # AutoComplete
            # Acs[None|All|Document|APIs]禁用自动补全提示功能|所有可用的资源|
            # 当前文档中出现的名称都自动补全提示|使用QsciAPIs类加入的名称都自动补全提示
            autoCompletionSource='AcsAll',  # 自动补全。对于所有Ascii字符
            autoCompletionCaseSensitivity=False,  # 自动补全大小写敏感,不是很有用
            autoCompletionThreshold=1,  # 输入多少个字符才弹出补全提示
            autoCompletionReplaceWord=True,#是否用补全的字符串替代光标右边的字符串

            # margins switch
            marginWidthes=((1,0), (3, 0), (4, 0)),  # 设置边栏宽度，设置宽度为0表示不显示
            marginWidth=(2, 12), # 设置边栏宽度

            # margin（line number）
            marginLineNumbers=(0, True),# 设置第0个边栏为行号边栏，True表示显示
            marginsForegroundColor=QColor('#ff0000ff'),
            marginsBackgroundColor=QColor('#ff0000ff'),  # 行号边栏背景颜色 不起作用？

            # margin (folding)
            # Folding: (No|Plain|Circled|Boxed|CircledTree|BoxedTree)FoldStyle
            folding="BoxedTreeFoldStyle",  # 代码可折叠
            foldMarginColors=(QColor('#aad'), QColor('#bbe')),
            ###marginType=(2,QsciScintilla.SC_MARGIN_SYMBOL),#页边类型
            ###marginMarkerMask=(2,QsciScintilla.SC_MASK_FOLDERS),#页边掩码
            ###marginSensitivity=(2,True),#注册通知事件，当用户点击边栏时，scintilla会通知我们

            # default highlightLang
            highlightLanguage='CSS',
        )

    ### Extensions

    def get_config(self, name, *args):
        """Return the current configuration setting for attribute ``name``.
        If ``name`` refers to an enumerated setting, return the string version
        of that enumeration.
        """
        getter = getattr(self, name)
        value = getter(*args)
        try:
            return EditorEnums.getName(value)
        except BadEnum:
            return value

    def set_config(self, name, value):
        """Set the current configuration setting for attribute ``getName``.
        """
        conf = {name: value}
        self.configure(**conf)

    def configure(self, **config):
        """Configure the editor with the given settings.
        Accepts ``keyword=getValue`` arguments for any attribute ``foo`` that is
        normally set via a ``setFoo`` method.
        For example, instead of this:
            >>> editor.setEdgeColor(QFont('Courier New', 10))
            >>> editor.setEolVisibility(True)
            >>> editor.setEdgeColumn(80)
        This method allows you to do this:
            >>> editor.configure(
            ...     edgeColor = QFont('Courier New', 10),
            ...     eolVisibility = True,
            ...     edgeColumn = 80)
        """
        self.settings.update(config)

        for name, args in config.items():
            # Get the setter method ('setWhatEver')
            setter = getattr(self, 'set' + name[0].upper() + name[1:])

            # Handle setters that accept multiple arguments
            # (like marginLineNumbers)
            if isinstance(args, (tuple, list)):
                setter(*args)
            # Convert strings to enum getValue
            elif type(args)==str and args in EditorEnums.dict:
                setter(EditorEnums.dict[args])
            # Single-argument setting
            else:
                setter(args)

        # Adjust margin if line numbers are on
        if 'marginLineNumbers' in config:
            if config['marginLineNumbers'] == (0, True):
                font_metrics = QtGui.QFontMetrics(self.settings['marginsFont'])#self.marginsFont())
                self.setMarginWidth(0, font_metrics.width('000') + 5)
            else:
                self.setMarginWidth(0, 0)

    # Language and syntax highlighting
    # Note: These follow the getter/setter pattern of other
    # QsciScintilla settings, to allow `configure` to manipulate them.
    def language(self):
        """Getter for language.
        """
        lexer = self.lexer()
        if lexer:
            return lexer.language()
        else:
            return 'None'

    def setHighlightLanguage(self, language):
        """Set syntax highlighting to the given language.
        If ``language`` is ``None``, ``'None'`` or empty, then
        syntax highlighting is disabled.
        """
        if not language or language == 'None':
            print("Disabling syntax highlighting")
            self.lexer = None
        else:
            print("%s syntax highlighting" % language)
            try:
                self.lexer = getattr(Qsci, 'QsciLexer'+language)(self)#lexer = QsciLexerCSS()
            except AttributeError:
                raise ValueError("Unknown language: '%s'" % language)
            self.lexer.setDefaultFont(self.font())
        self.setLexer(self.lexer)
        # high light code
        # self.lexer.setColor(QColor("#ffffff"))
        # self.lexer.setPaper(QColor("#333333"))
        # self.lexer.setColor(QColor("#5BA5F7"), QsciLexerPython.ClassName)
        # self.lexer.setColor(QColor("#FF0B66"), QsciLexerPython.Keyword)
        self.lexer.setColor(QColor("gray"), QsciLexerCSS.Comment)
        self.lexer.setFont(self.font(), QsciLexerCSS.Comment)
        # self.lexer.setColor(QColor("#BD4FE8"), QsciLexerPython.Number)
        # self.lexer.setColor(QColor("#F1E607"), QsciLexerPython.DoubleQuotedString)
        # self.lexer.setColor(QColor("#F1E607"), QsciLexerPython.TripleSingleQuotedString)
        # self.lexer.setColor(QColor("#F1E607"), QsciLexerPython.TripleDoubleQuotedString)
        # self.lexer.setColor(QColor("#F1E607"), QsciLexerPython.DoubleQuotedString)
        # self.lexer.setColor(QColor("#04F452"), QsciLexerPython.FunctionMethodName)
        # self.lexer.setColor(QColor("#FFFFFF"), QsciLexerPython.Operator)
        # self.lexer.setColor(QColor("#FFFFFF"), QsciLexerPython.Identifier)
        # self.lexer.setColor(QColor("#F1E607"), QsciLexerPython.CommentBlock)
        # self.lexer.setColor(QColor("#F1E607"), QsciLexerPython.UnclosedString)
        # self.lexer.setColor(QColor("#F1E607"), QsciLexerPython.HighlightedIdentifier)
        # self.lexer.setColor(QColor("#F1E607"), QsciLexerPython.Decorator)

        # marker
        # self.markerDefine(QsciScintilla.Minus, QsciScintilla.SC_MARKNUM_FOLDEROPEN)
        # self.markerDefine(QsciScintilla.Plus, QsciScintilla.SC_MARKNUM_FOLDER)
        # self.markerDefine(QsciScintilla.Minus, QsciScintilla.SC_MARKNUM_FOLDEROPENMID)
        # self.markerDefine(QsciScintilla.Plus, QsciScintilla.SC_MARKNUM_FOLDEREND)

        # marker define color
        # self.setMarkerBackgroundColor(QColor("#FFFFFF"), QsciScintilla.SC_MARKNUM_FOLDEREND)
        # self.setMarkerForegroundColor(QColor("#272727"), QsciScintilla.SC_MARKNUM_FOLDEREND)
        # self.setMarkerBackgroundColor(QColor("#FFFFFF"), QsciScintilla.SC_MARKNUM_FOLDEROPENMID)
        # self.setMarkerForegroundColor(QColor("#272727"), QsciScintilla.SC_MARKNUM_FOLDEROPENMID)
        # self.setMarkerBackgroundColor(QColor("#FFFFFF"),QsciScintilla.SC_MARKNUM_FOLDERMIDTAIL)
        # self.setMarkerForegroundColor(QColor("#272727"),QsciScintilla.SC_MARKNUM_FOLDERMIDTAIL)
        # self.setMarkerBackgroundColor(QColor("#FFFFFF"),QsciScintilla.SC_MARKNUM_FOLDERTAIL)
        # self.setMarkerForegroundColor(QColor("#272727"),QsciScintilla.SC_MARKNUM_FOLDERTAIL)
        # self.setMarkerBackgroundColor(QColor("#FFFFFF"), QsciScintilla.SC_MARKNUM_FOLDERSUB)
        # self.setMarkerForegroundColor(QColor("#272727"), QsciScintilla.SC_MARKNUM_FOLDERSUB)
        # self.setMarkerBackgroundColor(QColor("#FFFFFF"), QsciScintilla.SC_MARKNUM_FOLDER)
        # self.setMarkerForegroundColor(QColor("#272727"), QsciScintilla.SC_MARKNUM_FOLDER)
        # self.setMarkerBackgroundColor(QColor("#FFFFFF"), QsciScintilla.SC_MARKNUM_FOLDEROPEN)
        # self.setMarkerForegroundColor(QColor("#272727"), QsciScintilla.SC_MARKNUM_FOLDEROPEN)

        # self.SCI_MARKERDEFINE(QsciScintilla.SC_MARKNUM_FOLDEROPEN,QsciScintilla.SC_MARK_CHARACTER+65)#折叠标签样式
        # self.markerDefine(QsciScintilla.SC_MARKNUM_FOLDEROPEN, QsciScintilla.BoxedMinus)
        # self.markerDefine(QsciScintilla.SC_MARKNUM_FOLDEREND, QsciScintilla.SC_MARK_BOXPLUSCONNECTED)
        # self.markerDefine(QsciScintilla.SC_MARKNUM_FOLDEROPENMID, QsciScintilla.SC_MARK_BOXMINUSCONNECTED)
        # self.markerDefine(QsciScintilla.SC_MARKNUM_FOLDERMIDTAIL, QsciScintilla.SC_MARK_TCORNERCURVE)
        # self.markerDefine(QsciScintilla.SC_MARKNUM_FOLDERSUB, QsciScintilla.SC_MARK_VLINE)
        # self.markerDefine(QsciScintilla.SC_MARKNUM_FOLDERTAIL, QsciScintilla.SC_MARK_LCORNERCURVE)
        # 折叠标签颜色
        # self.setMarkerBackgroundColor(QColor("0xa0a0a0"),QsciScintilla.SC_MARKNUM_FOLDERSUB )
        # SendEditor(SCI_MARKERSETBACK, SC_MARKNUM_FOLDERMIDTAIL, 0xa0a0a0);
        # SendEditor(SCI_MARKERSETBACK, SC_MARKNUM_FOLDERTAIL, 0xa0a0a0);
        # SendEditor(SCI_SETFOLDFLAGS, 16 | 4, 0); // 如果折叠就在折叠行的上下各画一条横线

    def clear(self):
        """Clear the contents of the editor.
        """
        self.setText('')
        self.setModified(False)

    def load(self, filename):
        """Load the given file into the editor.
        """
        with open(filename, 'rb') as f:
            l=min(os.path.getsize(filename),500)
            bytes=f.read()
            self.coding=chardet0.detect(bytes[:l])['encoding']
            self.setText(bytes.decode(self.coding))
            self.setModified(False)
            self.setHighlightLanguage(self.guessLang(filename))

    def save(self, filename):
        """Save the editor contents to the given filename.
        """
        with open(filename, 'w') as outfile:
            outfile.write(self.text())
            self.setModified(False)

    ###
    ### Tools
    ###

    def guessLang(cls, filename):
        """Guess the language based on the given filename's extension, and return
        the getName of the language, or the string 'None' if no extension matches.
        """
        # Get the file's extension
        root, ext = os.path.splitext(filename)

        # See if any known language extensions match
        for language, extensions in language_extensions:
            if ext in extensions.split(' '):
                return language

        # No match -- asume plain text
        return 'None'

    ###
    ### The Missing Getters 只有set函数，但是没有对应get函数的属性
    ###

    def caretLineVisible(self):
        """Return the ``caretLineVisible`` attribute (True or False).
        """
        return self.SendScintilla(self.SCI_GETCARETLINEVISIBLE)

    def caretLineBackgroundColor(self):
        """Return the ``caretLineBackgroundColor`` as a QColor.
        """
        # TODO: Support alpha?
        bgr_int = self.SendScintilla(self.SCI_GETCARETLINEBACK)
        r, g, b = self.__BGRint2RGB(bgr_int)
        return QColor(r, g, b)

    def __BGRint2RGB(cls, bgr_int):
        """Convert an integer in BGR format to an ``(r, g, b)`` tuple.

        ``bgr_int`` is an integer representation of an RGB color, where the R, G,
        and B values are in the range (0, 255), and the three channels are comined
        into ``bgr_int`` by a bitwise ``red | (green << 8) | (blue << 16)``. This
        leaves the red channel in the least-significant bits, making a direct
        translation to a QColor difficult (the QColor constructor accepts an
        integer form, but it assumes the *blue* channel is in the least-significant
        bits).

        Examples:

            >>> __BGRint2RGB(4227327)
            (255, 128, 64)

        """
        red, green, blue = (
            bgr_int & 0xFF,
            (bgr_int >> 8) & 0xFF,
            (bgr_int >> 16) & 0xFF,
        )
        return (red, green, blue)
    ###
    ### extension Getters setter
    ###
    def setMarginWidthes(self,*widthes):
        for i,w in widthes:
           self.setMarginWidth(i,w)
