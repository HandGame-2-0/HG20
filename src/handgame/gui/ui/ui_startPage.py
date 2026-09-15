# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'startPage.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(655, 517)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalSpacer_5 = QSpacerItem(20, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.verticalSpacer_5, 6, 2, 1, 1)

        self.gameButton2 = QPushButton(Form)
        self.gameButton2.setObjectName(u"gameButton2")

        self.gridLayout.addWidget(self.gameButton2, 5, 2, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding)

        self.gridLayout.addItem(self.verticalSpacer_3, 2, 2, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding)

        self.gridLayout.addItem(self.verticalSpacer_4, 8, 2, 1, 1)

        self.horizontalSpacer = QSpacerItem(100, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 3, 0, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label, 1, 2, 1, 1)

        self.resultsButton = QPushButton(Form)
        self.resultsButton.setObjectName(u"resultsButton")

        self.gridLayout.addWidget(self.resultsButton, 7, 2, 1, 1)

        self.playButton = QPushButton(Form)
        self.playButton.setObjectName(u"playButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.playButton.sizePolicy().hasHeightForWidth())
        self.playButton.setSizePolicy(sizePolicy1)

        self.gridLayout.addWidget(self.playButton, 3, 2, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 2, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.verticalSpacer, 4, 2, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        self.gridLayout.addItem(self.verticalSpacer_2, 0, 2, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(100, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 3, 3, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.gameButton2.setText(QCoreApplication.translate("Form", u"Kalibracja Kamery", None))
        self.label.setText(QCoreApplication.translate("Form", u"HandGame 2.0", None))
        self.resultsButton.setText(QCoreApplication.translate("Form", u"Wyniki", None))
        self.playButton.setText(QCoreApplication.translate("Form", u"Graj", None))
    # retranslateUi

