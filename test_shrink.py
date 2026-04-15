import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QSize

app = QApplication(sys.argv)
w = QWidget()
l = QVBoxLayout(w)
lbl = QLabel()
lbl.setMinimumSize(1,1)
# Create a 500x500 green pixmap
pix = QPixmap(500,500)
pix.fill()
lbl.setPixmap(pix)
l.addWidget(lbl)
w.show()
w.resize(100, 100)
print('Window size after resize:', w.size())
