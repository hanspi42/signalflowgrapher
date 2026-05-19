from dependency_injector import providers, containers
from signalflowgrapher.gui.main_window import MainWindow
from signalflowgrapher.gui.graph_field import GraphField
from signalflowgrapher.controllers.main_controller import MainController
from signalflowgrapher.controllers.io_controller import IOController
from signalflowgrapher.controllers.operation_controller import \
    OperationController
from signalflowgrapher.model.model import Model
from signalflowgrapher.commands.command_handler import CommandHandler
from signalflowgrapher.gui.side_widget import SideWidget


class Models(containers.DeclarativeContainer):
    model = providers.Singleton(Model)


class CommandHandlers(containers.DeclarativeContainer):
    command_handler = providers.Singleton(CommandHandler)


class Controllers(containers.DeclarativeContainer):
    main_controller = providers.Singleton(MainController,
                                          Models.model,
                                          CommandHandlers.command_handler)
    io_controller = providers.Singleton(IOController,
                                        Models.model,
                                        CommandHandlers.command_handler)
    operation_controller = providers.Singleton(OperationController,
                                               Models.model,
                                               CommandHandlers.command_handler,
                                               main_controller)


class Views(containers.DeclarativeContainer):
    graph_field = providers.Singleton(GraphField,
                                      Controllers.main_controller,
                                      Models.model,
                                      CommandHandlers.command_handler)


class SideWidgets(containers.DeclarativeContainer):
    side_widget = providers.Singleton(SideWidget, Views.graph_field,
                                      Controllers.main_controller,
                                      Controllers.operation_controller,
                                      Controllers.io_controller,
                                      Models.model)


class MainWindows(containers.DeclarativeContainer):
    main_window = providers.Singleton(MainWindow,
                                      Views.graph_field,
                                      SideWidgets.side_widget,
                                      Controllers.main_controller,
                                      Controllers.io_controller,
                                      CommandHandlers.command_handler)
