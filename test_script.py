import sys

from PyQt5.QtWidgets import QApplication

from visual3D.vtkframe import VtkQtFrame

app = QApplication(sys.argv)
visVtkWidg =  VtkQtFrame()     
visVtkWidg.show()
sys.exit(app.exec_())