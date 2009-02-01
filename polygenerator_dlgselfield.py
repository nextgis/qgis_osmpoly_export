from PyQt4.QtCore import *
from PyQt4.QtGui import *

class dlgSelField(QDialog):
  def __init__(self, parent=None):
    QDialog.__init__(self)
    print "init"
    gr = QGroupBox(self)
    vbox = QVBoxLayout(gr)
    names = ['1','2','3']
    self.rbl = [QRadioButton(name, gr) for name in names]
    self.rbl[0].setChecked(True)
    for rb in self.rbl: vbox.addWidget(rb)
    gr.adjustSize()

    hbox = QHBoxLayout()
    pbnYes = QPushButton('Yes', self)
    pbnNo = QPushButton('No', self)
    hbox.addWidget(pbnYes)
    hbox.addWidget(pbnNo)

    layout = QVBoxLayout(self)
    layout.addWidget(gr)
    layout.addLayout(hbox)

    self.connect(pbnYes, SIGNAL("clicked()"), SLOT("accept()"))
    self.connect(pbnNo, SIGNAL("clicked()"), SLOT("reject()"))
  def selectedAttr(self):
    return [rb.text() for rb in self.rbl if rb.isChecked()]