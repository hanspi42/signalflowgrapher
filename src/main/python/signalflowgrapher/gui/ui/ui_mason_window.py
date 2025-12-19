# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mason_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QSizePolicy, QSpacerItem,
    QTextBrowser, QVBoxLayout, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(557, 547)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_output = QLabel(Dialog)
        self.label_output.setObjectName(u"label_output")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_output)

        self.txt_brw_output = QTextBrowser(Dialog)
        self.txt_brw_output.setObjectName(u"txt_brw_output")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.txt_brw_output)

        self.label_t_eval = QLabel(Dialog)
        self.label_t_eval.setObjectName(u"label_t_eval")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_t_eval)

        self.txt_brw_eval = QTextBrowser(Dialog)
        self.txt_brw_eval.setObjectName(u"txt_brw_eval")
        self.txt_brw_eval.setEnabled(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.txt_brw_eval)


        self.verticalLayout.addLayout(self.formLayout)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_message = QLabel(Dialog)
        self.label_message.setObjectName(u"label_message")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.label_message)

        self.horizontalSpacer = QSpacerItem(90, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.formLayout_2.setItem(0, QFormLayout.ItemRole.LabelRole, self.horizontalSpacer)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.buttonBox.accepted.connect(Dialog.accept)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Mason Output", None))
        self.label_output.setText(QCoreApplication.translate("Dialog", u"Output", None))
        self.label_t_eval.setText(QCoreApplication.translate("Dialog", u"Evaluated Output", None))
        self.label_message.setText(QCoreApplication.translate("Dialog", u"The output has been copied to the clipboard", None))
    # retranslateUi

