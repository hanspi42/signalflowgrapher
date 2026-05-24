# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'side_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, SideWidget):
        if not SideWidget.objectName():
            SideWidget.setObjectName(u"SideWidget")
        SideWidget.resize(321, 503)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SideWidget.sizePolicy().hasHeightForWidth())
        SideWidget.setSizePolicy(sizePolicy)
        self.main_vbox = QVBoxLayout(SideWidget)
        self.main_vbox.setObjectName(u"main_vbox")
        self.general_group = QGroupBox(SideWidget)
        self.general_group.setObjectName(u"general_group")
        sizePolicy.setHeightForWidth(self.general_group.sizePolicy().hasHeightForWidth())
        self.general_group.setSizePolicy(sizePolicy)
        self.general_group_layout = QGridLayout(self.general_group)
        self.general_group_layout.setObjectName(u"general_group_layout")
        self.btn_remove_nodes_and_branches = QPushButton(self.general_group)
        self.btn_remove_nodes_and_branches.setObjectName(u"btn_remove_nodes_and_branches")

        self.general_group_layout.addWidget(self.btn_remove_nodes_and_branches, 0, 0, 1, 1)


        self.main_vbox.addWidget(self.general_group)

        self.node_group = QGroupBox(SideWidget)
        self.node_group.setObjectName(u"node_group")
        sizePolicy.setHeightForWidth(self.node_group.sizePolicy().hasHeightForWidth())
        self.node_group.setSizePolicy(sizePolicy)
        self.node_layout = QFormLayout(self.node_group)
        self.node_layout.setObjectName(u"node_layout")
        self.node_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.lbl_node_name = QLabel(self.node_group)
        self.lbl_node_name.setObjectName(u"lbl_node_name")

        self.node_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_node_name)

        self.node_name = QLineEdit(self.node_group)
        self.node_name.setObjectName(u"node_name")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.node_name.sizePolicy().hasHeightForWidth())
        self.node_name.setSizePolicy(sizePolicy1)

        self.node_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.node_name)

        self.btn_insert_branch = QPushButton(self.node_group)
        self.btn_insert_branch.setObjectName(u"btn_insert_branch")

        self.node_layout.setWidget(2, QFormLayout.ItemRole.SpanningRole, self.btn_insert_branch)


        self.main_vbox.addWidget(self.node_group)

        self.branch_group = QGroupBox(SideWidget)
        self.branch_group.setObjectName(u"branch_group")
        sizePolicy.setHeightForWidth(self.branch_group.sizePolicy().hasHeightForWidth())
        self.branch_group.setSizePolicy(sizePolicy)
        self.branch_layout = QFormLayout(self.branch_group)
        self.branch_layout.setObjectName(u"branch_layout")
        self.branch_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.lbl_branch_weight = QLabel(self.branch_group)
        self.lbl_branch_weight.setObjectName(u"lbl_branch_weight")

        self.branch_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_branch_weight)

        self.branch_weight = QLineEdit(self.branch_group)
        self.branch_weight.setObjectName(u"branch_weight")
        sizePolicy1.setHeightForWidth(self.branch_weight.sizePolicy().hasHeightForWidth())
        self.branch_weight.setSizePolicy(sizePolicy1)

        self.branch_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.branch_weight)


        self.main_vbox.addWidget(self.branch_group)

        self.graph_operation_group = QGroupBox(SideWidget)
        self.graph_operation_group.setObjectName(u"graph_operation_group")
        sizePolicy.setHeightForWidth(self.graph_operation_group.sizePolicy().hasHeightForWidth())
        self.graph_operation_group.setSizePolicy(sizePolicy)
        self.graph_operation_layout = QGridLayout(self.graph_operation_group)
        self.graph_operation_layout.setObjectName(u"graph_operation_layout")
        self.btn_chaining_rule = QPushButton(self.graph_operation_group)
        self.btn_chaining_rule.setObjectName(u"btn_chaining_rule")

        self.graph_operation_layout.addWidget(self.btn_chaining_rule, 0, 0, 1, 1)

        self.btn_combine_parallel = QPushButton(self.graph_operation_group)
        self.btn_combine_parallel.setObjectName(u"btn_combine_parallel")

        self.graph_operation_layout.addWidget(self.btn_combine_parallel, 0, 1, 1, 1)

        self.btn_eliminate_node = QPushButton(self.graph_operation_group)
        self.btn_eliminate_node.setObjectName(u"btn_eliminate_node")

        self.graph_operation_layout.addWidget(self.btn_eliminate_node, 1, 0, 1, 1)

        self.btn_eliminate_self_loop = QPushButton(self.graph_operation_group)
        self.btn_eliminate_self_loop.setObjectName(u"btn_eliminate_self_loop")

        self.graph_operation_layout.addWidget(self.btn_eliminate_self_loop, 1, 1, 1, 1)

        self.btn_graph_transposition = QPushButton(self.graph_operation_group)
        self.btn_graph_transposition.setObjectName(u"btn_graph_transposition")

        self.graph_operation_layout.addWidget(self.btn_graph_transposition, 2, 0, 1, 1)

        self.btn_scale_path = QPushButton(self.graph_operation_group)
        self.btn_scale_path.setObjectName(u"btn_scale_path")

        self.graph_operation_layout.addWidget(self.btn_scale_path, 2, 1, 1, 1)

        self.btn_invert_path = QPushButton(self.graph_operation_group)
        self.btn_invert_path.setObjectName(u"btn_invert_path")

        self.graph_operation_layout.addWidget(self.btn_invert_path, 3, 0, 1, 1)


        self.main_vbox.addWidget(self.graph_operation_group)

        self.export_group = QGroupBox(SideWidget)
        self.export_group.setObjectName(u"export_group")
        sizePolicy.setHeightForWidth(self.export_group.sizePolicy().hasHeightForWidth())
        self.export_group.setSizePolicy(sizePolicy)
        self.export_layout = QGridLayout(self.export_group)
        self.export_layout.setObjectName(u"export_layout")
        self.btn_generate_mason = QPushButton(self.export_group)
        self.btn_generate_mason.setObjectName(u"btn_generate_mason")

        self.export_layout.addWidget(self.btn_generate_mason, 0, 0, 1, 1)

        self.btn_generate_tikz = QPushButton(self.export_group)
        self.btn_generate_tikz.setObjectName(u"btn_generate_tikz")

        self.export_layout.addWidget(self.btn_generate_tikz, 1, 0, 1, 1)


        self.main_vbox.addWidget(self.export_group)


        self.retranslateUi(SideWidget)

        QMetaObject.connectSlotsByName(SideWidget)
    # setupUi

    def retranslateUi(self, SideWidget):
        SideWidget.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.general_group.setTitle(QCoreApplication.translate("Form", u"General", None))
#if QT_CONFIG(tooltip)
        self.btn_remove_nodes_and_branches.setToolTip(QCoreApplication.translate("Form", u"Select nodes or branches", None))
#endif // QT_CONFIG(tooltip)
        self.btn_remove_nodes_and_branches.setText(QCoreApplication.translate("Form", u"Remove", None))
        self.node_group.setTitle(QCoreApplication.translate("Form", u"Node options", None))
        self.lbl_node_name.setText(QCoreApplication.translate("Form", u"Name", None))
#if QT_CONFIG(tooltip)
        self.btn_insert_branch.setToolTip(QCoreApplication.translate("Form", u"Select one or two nodes", None))
#endif // QT_CONFIG(tooltip)
        self.btn_insert_branch.setText(QCoreApplication.translate("Form", u"Insert branch", None))
        self.branch_group.setTitle(QCoreApplication.translate("Form", u"Branch options", None))
        self.lbl_branch_weight.setText(QCoreApplication.translate("Form", u"Weight", None))
        self.graph_operation_group.setTitle(QCoreApplication.translate("Form", u"Graphoperations", None))
#if QT_CONFIG(tooltip)
        self.btn_chaining_rule.setToolTip(QCoreApplication.translate("Form", u"Select two subsequent branches", None))
#endif // QT_CONFIG(tooltip)
        self.btn_chaining_rule.setText(QCoreApplication.translate("Form", u"Chaining rule", None))
#if QT_CONFIG(tooltip)
        self.btn_combine_parallel.setToolTip(QCoreApplication.translate("Form", u"Select two parallel branches", None))
#endif // QT_CONFIG(tooltip)
        self.btn_combine_parallel.setText(QCoreApplication.translate("Form", u"Combine parallel", None))
#if QT_CONFIG(tooltip)
        self.btn_eliminate_node.setToolTip(QCoreApplication.translate("Form", u"Select one node which can be eliminated", None))
#endif // QT_CONFIG(tooltip)
        self.btn_eliminate_node.setText(QCoreApplication.translate("Form", u"Eliminate node", None))
#if QT_CONFIG(tooltip)
        self.btn_eliminate_self_loop.setToolTip(QCoreApplication.translate("Form", u"Select a branch which is a self-loop", None))
#endif // QT_CONFIG(tooltip)
        self.btn_eliminate_self_loop.setText(QCoreApplication.translate("Form", u"Eliminate self-loop", None))
        self.btn_graph_transposition.setText(QCoreApplication.translate("Form", u"Graph transposition", None))
#if QT_CONFIG(tooltip)
        self.btn_scale_path.setToolTip(QCoreApplication.translate("Form", u"Select one or multiple nodes", None))
#endif // QT_CONFIG(tooltip)
        self.btn_scale_path.setText(QCoreApplication.translate("Form", u"Scale path", None))
#if QT_CONFIG(tooltip)
        self.btn_invert_path.setToolTip(QCoreApplication.translate("Form", u"Select a branch that has a start node with zero ingoing branches", None))
#endif // QT_CONFIG(tooltip)
        self.btn_invert_path.setText(QCoreApplication.translate("Form", u"Invert path", None))
        self.export_group.setTitle(QCoreApplication.translate("Form", u"Exports", None))
#if QT_CONFIG(tooltip)
        self.btn_generate_mason.setToolTip(QCoreApplication.translate("Form", u"Select a start and a end node", None))
#endif // QT_CONFIG(tooltip)
        self.btn_generate_mason.setText(QCoreApplication.translate("Form", u"Generate Mason", None))
        self.btn_generate_tikz.setText(QCoreApplication.translate("Form", u"Generate TikZ", None))
    # retranslateUi

