# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 394)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.saveButton = QPushButton(Form)
        self.saveButton.setObjectName(u"saveButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.saveButton.sizePolicy().hasHeightForWidth())
        self.saveButton.setSizePolicy(sizePolicy)
        self.saveButton.setMinimumSize(QSize(0, 25))

        self.gridLayout.addWidget(self.saveButton, 5, 0, 1, 1)

        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QSize(0, 25))

        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)

        self.resComboBox = QComboBox(Form)
        self.resComboBox.setObjectName(u"resComboBox")

        self.gridLayout.addWidget(self.resComboBox, 1, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 3, 0, 1, 1)

        self.fullScreenCheckBox = QCheckBox(Form)
        self.fullScreenCheckBox.setObjectName(u"fullScreenCheckBox")
        self.fullScreenCheckBox.setLocale(QLocale(QLocale.Polish, QLocale.Poland))

        self.gridLayout.addWidget(self.fullScreenCheckBox, 2, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.saveButton.setText(QCoreApplication.translate("Form", u"Save", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Rozdzielczo\u015b\u0107", None))
        self.fullScreenCheckBox.setText(QCoreApplication.translate("Form", u"Pe\u0142ny Ekran", None))
    # retranslateUi

