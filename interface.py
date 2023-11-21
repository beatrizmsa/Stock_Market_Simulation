from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
from environment import Environment
from datetime import timedelta
import socket
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Define the size of the interface
HEIGTH = 800
WIDTH = 1000


class InterfaceAgent:
    def __init__(self, window, env):
        self.environment = env
        self.window = window
        self.agent_id = {"Alexandre": "broker_agent@localhost", "Beatriz": "broker@localhost",
                         "João": "trading_agent@localhost", "Pedro": "random_agent@localhost",
                         "Maria": "broker_agent2@localhost", "Helena": "altorisco@localhost"}
        self.portfolio = [self.environment.get_portfolio_value(agent_id) for agent, agent_id in self.agent_id.items()]
        self.color_variations = ["#FF7667", "#FFD575", "#71DDFF", "#53ED7F", "#6690FF", "#C3496E"]
        self.current_agent_id = None
        self.window.title('Agent Interface')
        self.window.geometry(f"1000x800")
        self.window.resizable(width=False, height=False)
        self.window.config(background='#37465B')
        self.window.protocol("WM_DELETE_WINDOW", self.exit)
        self.stock_label = []
        self.agent_profile = []
        self.agent_broker = []

        # Create the body for the interface
        self.body = Frame(self.window, bg='#37465B')
        self.body.place(x=0, y=0, width=WIDTH, height=HEIGTH)

        # Initialize the graph for the stocks for the profile of the agents
        self.agent_stocks = Frame(self.body, bg='#37465B')
        self.agent_stocks.grid(column=0, row=0, sticky='nsew')
        self.agent_stocks.place(x=WIDTH - 200, y=60)
        self.fig, self.ax = plt.subplots(figsize=(5, 4), facecolor='#37465B')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.agent_stocks)
        self.canvas.get_tk_widget().grid(column=450, row=500, sticky='nsew')
        self.agent_stocks.place_forget()

        # Initialize the graph for the portfolio and stocks of all agents
        self.graph_portfolio = Frame(self.body, bg='#37465B')
        self.graph_portfolio.grid(column=0, row=0, sticky='nsew')
        self.graph_stocks = Frame(self.body, bg='#37465B')
        self.graph_stocks.grid(column=0, row=0, sticky='nsew')

        # Create the upper bar for the interface
        self.bar = Frame(self.window, bg='#212B38')
        self.bar.place(x=0, y=0, width=WIDTH, height=60)

        # Create the label displaying the day
        date = self.environment.time_start + timedelta(self.environment.day_interval)
        self.day = Label(self.bar, text=date.strftime('%d-%m-%Y'), bg='#212B38', font=("#54FFE7", 13, "bold"),
                         bd=0, width=30, height=3, highlightbackground='#212B38', fg='#54FFE7')
        self.day.place(x=(WIDTH/2)-180, y=-4)

        # Create the button to go to the messages
        self.message = Button(self.bar, text="Messages", bg='#212B38', font=("#54FFE7", 13, "bold"),
                              bd=0, width=20, height=3, highlightbackground='#212B38', activebackground='#212B38',
                              fg='#54FFE7', command=lambda: self.show_messages())
        self.message.place(x=800, y=-8)

        # Create the button to go to the home page
        home_image = Image.open('images/home.png')
        resized_image = home_image.resize((40, 40))
        photo = ImageTk.PhotoImage(resized_image)
        self.home = Button(self.bar, image=photo, bg='#212B38', font=("#54FFE7", 15, "bold"), bd=0, fg='#54FFE7',
                           highlightbackground='#212B38', activebackground='#212B38', command=lambda: self.show_home())
        self.home.image = photo
        self.home.place(x=83, y=10)

        # Create the button to update the data
        self.update = Button(self.bar, text="Update", bg='#212B38', font=("#54FFE7", 13, "bold"), bd=0, width=20,
                             height=3, highlightbackground='#212B38', activebackground='#212B38',
                             fg='#54FFE7', command=lambda: self.refresh_data())
        self.update.place(x=600, y=-8)

        # Create the label to display the messages
        self.messages_label = Label(self.body, text="", bg='#37465B', fg='#ffffff', font=("", 13, "bold"))
        self.messages_label.place(x=300, y=500)
        self.messages_label.place_forget()

        # Create the table to display the agent data
        self.tree = ttk.Treeview(self.body, columns=('Variable', 'Value'), show='headings', height=3)
        self.tree.place(x=300, y=500)
        self.tree.column('Variable', anchor=W, width=150)
        self.tree.column('Value', anchor=W, width=150)
        self.tree.heading('Variable', text='Variable', anchor=W)
        self.tree.heading('Value', text='Value', anchor=W)
        self.tree.place_forget()

        # Create the home page
        self.create_home_page()

        #  Create the sidebar with the agents buttons
        self.sidebar = Frame(self.body, bg='#212B38')
        self.sidebar.place(x=0, y=0, width=200, height=HEIGTH)

        i = 0
        for agent, agent_id in self.agent_id.items():
            agent_button = Button(self.sidebar, text=agent, bg=self.color_variations[i], font=("", 14, "bold"), bd=0,
                                  width=14, height=3, highlightbackground='#212B38', activebackground='#ffffff',
                                  command=lambda a=agent_id: self.show_agent_variables(a, 0))
            agent_button.place(x=11, y=80 + i*120)
            i += 1

        self.window.mainloop()

    # Create the home page for the interface
    def create_home_page(self):
        # Hide the unwanted information for this page
        self.graph_portfolio.place_forget()
        self.graph_stocks.place_forget()
        self.window.update_idletasks()

        # Create the graph with the portfolio value for all agents
        self.graph_portfolio.place(x=250, y=60)
        fig, ax = plt.subplots(1, 1, dpi=80, figsize=(9, 4), sharey=True, facecolor='#37465B')
        ax.set_facecolor('#37465B')
        ax.bar(self.agent_id.keys(), self.portfolio, color=self.color_variations)
        ax.set_xlabel('Agents')
        ax.set_ylabel('Value of the stocks')
        ax.set_title('Portfolio value', color='#ffffff', size=13, fontweight='bold')
        plt.setp(ax.get_xticklabels(), color='#ffffff', size=13, fontweight='bold')
        plt.setp(ax.get_yticklabels(), color='#ffffff', size=13, fontweight='bold')
        ax.xaxis.label.set_color('#ffffff')
        ax.yaxis.label.set_color('#ffffff')
        canvas = FigureCanvasTkAgg(fig, master=self.graph_portfolio)
        canvas.draw()
        canvas.get_tk_widget().grid(column=0, row=0, sticky='nsew')

        # Create the stocks graph of the home page that displays information of the last 30 days
        self.graph_stocks.place(x=250, y=400)
        stocks = ["META", "AAPL", "TSLA", "GOOGL"]
        if self.environment.day_interval < 30:
            datas = [self.environment.time_start + timedelta(days=i) for i in range(self.environment.day_interval+1)
                     if (self.environment.time_start + timedelta(days=i)).weekday() < 5]
            data_start = self.environment.time_start
            data_end = self.environment.time_start + timedelta(self.environment.day_interval)
        else:
            data_end = self.environment.time_start + timedelta(self.environment.day_interval)
            data_start = data_end - timedelta(30)
            datas = [data_start + timedelta(days=i) for i in range(31)
                     if (data_start + timedelta(days=i)).weekday() < 5]
        stocks1 = self.environment.get_stock_days(stocks[0], data_start, data_end)
        stocks2 = self.environment.get_stock_days(stocks[1], data_start, data_end)
        stocks3 = self.environment.get_stock_days(stocks[2], data_start, data_end)
        stocks4 = self.environment.get_stock_days(stocks[3], data_start, data_end)

        if len(datas) > len(stocks1):
            for i in range(len(datas)-len(stocks1)):
                datas.pop(0)

        fig, ax = plt.subplots(1, 1, dpi=80, figsize=(9, 4), facecolor='#37465B')
        ax.set_facecolor('#37465B')
        ax.plot(datas, stocks1, marker='o', label=stocks[0], color='#08C6AB')
        ax.plot(datas, stocks2, marker='o', label=stocks[1], color='#FF5733')
        ax.plot(datas, stocks3, marker='o', label=stocks[2], color='#B22A00')
        ax.plot(datas, stocks4, marker='o', label=stocks[3], color='#FFD500')
        ax.set_xticks([datas[0], datas[-1]])
        ax.set_xticklabels([datas[0].strftime('%Y-%m-%d'), datas[-1].strftime('%Y-%m-%d')])
        ax.set_xlabel('Data')
        ax.set_ylabel('Stocks')
        plt.setp(ax.get_xticklabels(), color='#ffffff', size=13, fontweight='bold')
        plt.setp(ax.get_yticklabels(), color='#ffffff', size=13, fontweight='bold')
        ax.xaxis.label.set_color('#ffffff')
        ax.yaxis.label.set_color('#ffffff')
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        ax.legend(loc='upper right')
        ax.set_title('Change of the stocks value ', color='#ffffff', size=13, fontweight='bold')

        canvas = FigureCanvasTkAgg(fig, master=self.graph_stocks)
        canvas.draw()
        canvas.get_tk_widget().grid(column=0, row=0, sticky='nsew')

        self.window.update_idletasks()

    # Show the main menu
    def show_home(self):
        self.current_agent_id = None
        self.tree.place_forget()
        self.agent_stocks.place_forget()
        self.window.update_idletasks()
        self.messages_label.place_forget()
        for agent in self.agent_profile:
            agent.place_forget()

        for agent in self.agent_broker:
            agent.place_forget()
        for label in self.stock_label:
            label.place_forget()
        self.graph_stocks.place(x=250, y=410)
        self.graph_portfolio.place(x=250, y=60)
        self.window.update_idletasks()

    # Show the menu to display the messages
    def show_messages(self):
        self.current_agent_id = None
        global global_messages
        # Hide the label first
        self.messages_label.place_forget()

        self.tree.place_forget()
        self.graph_stocks.place_forget()
        self.graph_portfolio.place_forget()
        self.agent_stocks.place_forget()
        for agent in self.agent_profile:
            agent.place_forget()
        for agent in self.agent_broker:
            agent.place_forget()
        for label in self.stock_label:
            label.place_forget()
        self.window.update_idletasks()

        # Display the messages
        messages_text = "\n".join(global_messages)
        self.messages_label.config(text=messages_text)
        self.messages_label.place(x=200, y=100)

        # Clear the messages after displaying
        global_messages = []

    # Show the information for each agent
    def show_agent_variables(self, agent_id, refresh):
        self.messages_label.place_forget()
        self.graph_portfolio.place_forget()
        self.graph_stocks.place_forget()
        self.messages_label.place_forget()
        self.window.update_idletasks()
        self.create_profile_page(agent_id, refresh)

    # Create the profile pages for the agents
    def create_profile_page(self, agent_id, refresh):
        if self.current_agent_id != agent_id or refresh == 1:

            # Hide the unwanted graphs and labels when showing the profile of an agent
            self.agent_stocks.place_forget()
            self.tree.place_forget()
            for agent in self.agent_profile:
                agent.place_forget()

            for agent in self.agent_broker:
                agent.place_forget()

            for label in self.stock_label:
                label.place_forget()
            self.ax.clear()

            for item in self.tree.get_children():
                self.tree.delete(item)
            self.window.update_idletasks()

            # Get the variables for each agent
            agent_variables = {
                'Remaining Cash': self.environment.get_remaining_cash(agent_id),
                'Portfolio Value': self.environment.get_portfolio_value(agent_id),
                'Total Value': self.environment.get_total_value(agent_id),
            }

            # Add the variables to the table
            for variable, value in agent_variables.items():
                self.tree.insert('', END, values=(variable, value))
            self.tree.place(x=230, y=270)
            self.current_agent_id = agent_id

            # Add the graph for the owned stocks of the agent
            stocks = list(self.environment.owned_stocks[agent_id].keys())
            quantities = list(self.environment.owned_stocks[agent_id].values())
            found_agent = next(
                (agent for agent, agent_id in self.agent_id.items() if agent_id == self.current_agent_id), None)
            agent_keys = list(self.agent_id.keys())
            index = agent_keys.index(found_agent)
            self.ax.bar(stocks, quantities, color=self.color_variations[index], label=f'{found_agent} - {agent_id}')
            self.ax.set_facecolor('#37465B')
            self.ax.set_ylabel('Number of Shares')
            self.ax.set_xlabel('Stocks')
            self.ax.set_title('Owned Stocks', color='#ffffff', size=7)
            self.ax.legend(loc='upper right')  
            plt.setp(self.ax.get_xticklabels(), color='#ffffff', size=9)
            plt.setp(self.ax.get_yticklabels(), color='#ffffff', size=9)
            self.canvas.draw()  
            self.agent_stocks.place(x=500, y=350)

            # Add the profile picture and the name of the agents
            name_agent = ""
            for agent_name, agent in self.agent_id.items():
                if agent == self.current_agent_id:
                    name_agent = agent_name
            agent_image = Image.open(f'images/profile_{index}.png')
            resized_image = agent_image.resize((120, 120))
            photo = ImageTk.PhotoImage(resized_image)
            agent = Label(self.body,  compound="left", image=photo, text=name_agent, bg='#37465B',
                          fg='#ffffff', font=("#54FFE7", 13, "bold"), bd=0, highlightbackground='#37465B')
            agent.image = photo
            agent.place(x=230, y=90)
            self.agent_profile.append(agent)

            # Add the profile of the broker agents to the broker profile
            if agent_id == 'broker@localhost':
                i = 0
                for other_agent, other_agent_id in self.agent_id.items():
                    if other_agent_id == 'broker_agent2@localhost' or other_agent_id == 'broker_agent@localhost':
                        index = agent_keys.index(other_agent)
                        agent_broker = Image.open(f'images/profile_{index}.png')
                        resized_image = agent_broker.resize((60, 60))
                        photo = ImageTk.PhotoImage(resized_image)
                        agent = Button(self.body, compound="left", image=photo, text=other_agent, bg='#37465B',
                                       fg='#ffffff', font=("#54FFE7", 13, "bold"), bd=0, highlightbackground='#37465B',
                                       activebackground='#37465B',
                                       command=lambda a=other_agent_id: self.show_agent_variables(a, 0))
                        agent.image = photo
                        agent.place(x=700, y=80+i*100)
                        self.agent_broker.append(agent)
                        i += 1

            # Show if the stocks are going up or down based on the current price and price when the agent bought
            i = 0
            for stock in stocks:
                if self.environment.get_stock_buying_value(agent_id, stock) > self.environment.get_stock_value(stock):
                    agent_broker = Image.open(f'images/price_down.png')
                    resized_image = agent_broker.resize((40, 40))
                    photo = ImageTk.PhotoImage(resized_image)
                    my_label = Label(self.body, text=stock, compound="left", image=photo, bg='#37465B',
                                     font=("#54FFE7", 13, "bold"), bd=0, highlightbackground='#37465B')
                    my_label.imagem = photo
                    my_label.place(x=230, y=380 + i*60)
                    i += 1
                    self.stock_label.append(my_label)
                else:
                    agent_broker = Image.open(f'images/price_up.png')
                    resized_image = agent_broker.resize((40, 40))
                    photo = ImageTk.PhotoImage(resized_image)
                    my_label = Label(self.body, text=stock, compound="left", image=photo, bg='#37465B',
                                     font=("#54FFE7", 13, "bold"), bd=0, highlightbackground='#37465B')
                    my_label.imagem = photo
                    my_label.place(x=230, y=380 + i*60)
                    i += 1
                    self.stock_label.append(my_label)
            
            self.window.update_idletasks()

    # Function to update the data
    def refresh_data(self):
        self.environment.load_from_file()
        self.portfolio = [self.environment.get_portfolio_value(agent_id) for agent_id in self.agent_id.values()]
        self.refresh_interface_data()

    # Function to update the graphs
    def refresh_interface_data(self):
        date = self.environment.time_start + timedelta(self.environment.day_interval)
        self.day = Label(self.bar, text=date.strftime('%d-%m-%Y'), bg='#212B38', font=("#54FFE7", 13, "bold"), bd=0,
                         width=30, height=3, highlightbackground='#212B38', fg='#54FFE7')
        self.day.place(x=(WIDTH/2)-180, y=-4)
        if self.current_agent_id is None:
            self.create_home_page()
        else:
            self.show_agent_variables(self.current_agent_id, 1)

    # Function to exit the interface
    def exit(self):
        self.window.quit()


global_messages = []


# Class to receive the messages from the stock market
class InterfaceServer:
    def __init__(self):
        self.server_socket = None
        self.stop_threads = False

    # Start the interface that connects to the stock market
    def start_interface(self):
        host = '127.0.0.1'
        port = 12345

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)

        print(f"Interface listening on {host}:{port}")

        while not self.stop_threads:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except:
                break

    # Function to handle the client and receive the messages
    def handle_client(self, client_socket):
        global global_messages
        while not self.stop_threads:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"Received: {data}")
                if data == "Received: The week has ended":
                    pass
                global_messages.append(data)
            except Exception as e:
                print(f"Error handling client: {e}")
                break

        client_socket.close()

    # Function to stop the interface
    def stop_interface(self):
        self.stop_threads = True
        if self.server_socket:
            self.server_socket.close()
            print("Interface stopped")


# Function to check if the interface thread has stopped
def check_stop_thread(interface_server, interface_thread, windows):
    if not interface_server.stop_threads:
        windows.after(100, check_stop_thread, interface_server, interface_thread)
    else:
        windows.quit()


if __name__ == "__main__":
    windows = Tk()
    environment = Environment()
    environment.load_from_file()
    interface_server = InterfaceServer()
    interface_thread = threading.Thread(target=interface_server.start_interface)
    interface_thread.start()

    # Create and run the Dashboard
    dashboard = InterfaceAgent(windows, environment)

    # When the Dashboard is closed, stop the interface thread
    interface_server.stop_interface()
    interface_thread.join()

    # Periodically check if the interface thread has stopped
    windows.after(100, check_stop_thread, interface_server, interface_thread, windows)

    # Start the Tkinter main loop
    windows.mainloop()
