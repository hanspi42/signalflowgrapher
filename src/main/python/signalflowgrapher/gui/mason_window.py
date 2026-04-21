from PySide6.QtWidgets import QDialog, QApplication
from signalflow_algorithms.algorithms.mason import MasonResult
from signalflowgrapher.gui.ui.ui_mason_window import Ui_Dialog as Ui_MasonWindow
from sympy.printing.lambdarepr import lambdarepr


class MasonWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Load UI from generated class
        self._ui = Ui_MasonWindow()
        self._ui.setupUi(self)
        self.__non_simplified_result = None
        self._ui.btn_simplify.setEnabled(False)
        self._ui.btn_simplify.clicked.connect(self.simplify_result)

    def set_content(self, interim_res: MasonResult):
        # Build strings based on mason result
        sympy_import_name = 'sp'
        interim_strs = {
            'det': 'determinant = {}'.format(lambdarepr(
                interim_res.determinant)),
            'paths': 'paths = {}'.format(lambdarepr(interim_res.paths)),
            'loops': 'loops = {}'.format(lambdarepr(interim_res.loops)),
            'numerator': 'numerator = {}'.format(
                lambdarepr(interim_res.numerator)),
            'denominator': 'denominator = {}'.format(
                lambdarepr(interim_res.denominator)),
            'transfer_function': 'transfer_function = {}'.format(
                lambdarepr(interim_res.transfer_function))
        }

        # Create full formula without simplifying
        T = interim_res.transfer_function[0][0]
        non_simplified = T.subs(interim_res.transfer_function) \
            .subs(interim_res.numerator) \
            .subs(interim_res.denominator) \
            .subs(interim_res.determinant) \
            .subs(interim_res.paths) \
            .subs(interim_res.loops)
        self.__non_simplified_result = non_simplified

        t_evaluated_str = str(non_simplified)

        # Combine all symbols to be on top for combined output, except the
        # symbols of the forward paths
        combined_symbols = ''
        combined_symbols += self.__get_symbols_str_from_interim_res(
            interim_res.determinant, sympy_import_name)
        combined_symbols += self.__get_symbols_str_from_interim_res(
            interim_res.loops, sympy_import_name)
        combined_symbols += self.__get_symbols_str_from_interim_res(
            interim_res.numerator, sympy_import_name)
        combined_symbols += self.__get_symbols_str_from_interim_res(
            interim_res.denominator, sympy_import_name)
        combined_symbols += self.__get_symbols_str_from_interim_res(
            interim_res.transfer_function, sympy_import_name)
        combined_symbols += self.__get_symbols(
            list(map(lambda x: str(x), non_simplified.free_symbols)),
            sympy_import_name)

        # Symbols of the forward path
        path_symbols = self.__get_symbols_str_from_interim_res(
            interim_res.paths, sympy_import_name)

        # Now build the code that will be copied to the clipboard
        # .. Import of sympy
        combined_output = 'import sympy as {}\n'.format(sympy_import_name)
        # .. all symbol definitions except for forward path
        combined_output += combined_symbols

        # calculation of the graph determinant
        interim_outputs = '\n{loops}\n{det}\n{denominator}'
        combined_output += interim_outputs.format_map(interim_strs)

        # calculation of the forward path
        interim_outputs = '{paths}\n{numerator}'
        combined_output += '\n\n'
        combined_output += path_symbols
        combined_output += interim_outputs.format_map(interim_strs)

        # calculation of transfer function
        interim_outputs = '\n\n{transfer_function}'
        combined_output += interim_outputs.format_map(interim_strs)
        combined_output += '\nT=' + str(interim_res.transfer_function[0][0])
        combined_output += '.subs(transfer_function).subs(numerator)'
        combined_output += '.subs(denominator).subs(determinant).subs(paths)'
        combined_output += '.subs(loops)     #optional: add .simplify() to simplify the result'
        combined_output += '\ndisplay(T)'

        # Set combined output to clipboard
        QApplication.clipboard().setText(combined_output)

        # Set combined output to text browser
        self._ui.txt_brw_output.setPlainText(combined_output)

        # Set evaluated result to text browser
        self._ui.txt_brw_eval.setPlainText(t_evaluated_str)
        self._ui.btn_simplify.setEnabled(True)

    def simplify_result(self):
        # Simplify only on explicit user request.
        if self.__non_simplified_result is None:
            return

        simplified_result = self.__non_simplified_result.simplify()
        self._ui.txt_brw_eval.setPlainText(str(simplified_result))
        self._ui.btn_simplify.setEnabled(False)

    def __get_symbols_str_from_interim_res(self,
                                           expressions,
                                           sympy_import_name) -> str:
        # Create a sympy symbols command for interim result
        if len(expressions) == 0:
            return ''

        symbols = list(map(lambda e: lambdarepr(e[0]), expressions))
        return self.__get_symbols(symbols, sympy_import_name)

    def __get_symbols(self, symbols, sympy_import_name) -> str:
        # Create sympy symbols command for given symbols
        if len(symbols) == 0:
            return ''

        joined = ','.join(symbols)
        return '{} = {}.symbols(\'{}\')\n'.format(joined,
                                                  sympy_import_name,
                                                  joined)
