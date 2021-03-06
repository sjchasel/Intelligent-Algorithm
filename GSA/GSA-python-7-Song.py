import numpy as np
import random
import time
import matplotlib.pyplot as plt


plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def fun1(x:np.ndarray):
    # 一维
    return abs(0.2 * x) + 10 * np.sin(5 * x) + 7 * np.cos(4 * x)

def fun2(x:np.ndarray):
    # 一维
    return 0.1 * x ** 2 - np.cos( 2 * np.pi * x) + 1


def Griewangk(x:np.ndarray):
    # 任意维
    sum2 = 1
    for i in range(x.shape[0]):
        a = np.cos(x[i] / np.sqrt(i + 1))
        sum2 = sum2 * a
    return 1 + sum(x ** 2) / 4000 - sum2


def Rastrigrin(x:np.ndarray):
    # 任意维
    return 10 * x.shape[0] + sum(x ** 2 - 10 * np.cos(2 * np.pi * x))

class GSA():


    def __init__(self,T_max=400,T_min=10,pop=10,new_pop=10,cur_g=1,p=0.9,tour_n=10,func=fun1,shape=1, **kwargs):
        """
        @param T_max: 最大温度
        @param T_min: 最小温度
        @param pop: 种群的个体数量
        @param new_pop: 每个个体生成的新解的数量
        @param cur_g: 当前迭代代数
        @param p: 锦标赛中的概率p
        @param tour_n: 一次锦标赛的选手数
        @param func: 函数
        @param x_best: 最优点
        @param y_best: 最优点的函数值
        @param shape: x的维度
        """
        self.T_max = T_max
        self.T = T_max  # 当前温度
        self.T_min = T_min
        self.pop = pop
        self.new_pop = new_pop
        self.cur_g = cur_g
        self.p = p
        self.tour_n = tour_n
        self.func = func
        self.shape = shape
        self.x_best = [0]*shape
        self.y_best = 0
        self.x_history = []
        self.T_history = [self.T]
        self.m, self.n, self.quench = kwargs.get('m', 1), kwargs.get('n', 1), kwargs.get('quench', 1)
        self.lower, self.upper = kwargs.get('lower', -10), kwargs.get('upper', 10)
        self.c = self.m * np.exp(-self.n * self.quench)
        self.y_best_history = []



    def xrange(self, xmin: np.ndarray, xmax: np.ndarray):  # 输入x范围，尚未考虑多维情形
        self.xmin = xmin
        print('x的下界是'+str(xmin))
        self.xmax = xmax
        print('x的上界是'+str(xmax))



    def init_pop(self):
        pop1 = []
        for i in range(self.pop):
            self.x_init = self.xmin + np.random.uniform(0,1,self.shape) * (self.xmax - self.xmin)
            pop1.append(np.array(self.x_init))
        # x_init = [1]*self.shape
        # for i in range(self.pop):
        #     pop1.append(self.fast_get(x_init))
        return pop1

    def judge(self, df):
        if df < 0:  # 新解 < 原解 ---> 直接接受
            return True
        else:
            pp = np.exp(-1 * (df / self.T))  # 新解 > 原解 ---> 计算接受概率p
            rand_p = random.random()  # 产生 rand_p ~ Uniform(0, 1)
            if pp > rand_p:
                return True
            else:
                return False

    def fast_get(self,x):
        r = np.random.uniform(-1, 1, size=self.shape)
        xc = np.sign(r) * self.T * ((1 + 1.0 / self.T) ** np.abs(r) - 1.0)
        x_new = x + xc * (self.upper - self.lower)
        return x_new


    def generate(self,old_pop):
        x_new = []

        for i in range(len(old_pop)):
            while len(x_new) < (i+1)*self.new_pop:
                xnew = self.fast_get(old_pop[i])

                # Metropolis准则
                # print('old_pop[i]是'+str(old_pop[i]))
                df = self.func(xnew) - self.func(old_pop[i])  # 计算函数值差值
                if self.judge(df):
                    x_new.append(xnew)

        return x_new

    def tournament(self,x):
        """
        计算每个点的适应值，选择N个点作为生存集（GA）锦标赛。
        如果适应值最大的点被舍弃了，那么就随机舍弃一个点，又把它加回来。
        处理为先把适应值最大的点加进去
        """
        survive = []
        x_cur = x
        y_cur = [self.func(xx) for xx in x]
        best_index = y_cur.index(min(y_cur))
        self.x_best = x_cur[best_index]
        self.y_best = y_cur[best_index]
        survive.append(self.x_best)  # 先把最好的点放进去
        del(x_cur[best_index])  # 把最好的点删了，其他的进行锦标赛，最后选出self.pop-1个点

        #     进行选择（锦标赛方法）
        #     choose k (the tournament size) individuals from the population at random
        #     choose the best individual from the tournament with probability p
        #     choose the second best individual with probability p*(1-p)
        #     choose the third best individual with probability p*((1-p)^2)
        #     and so on

        fitness = [self.y_best - self.func(xx) for xx in x_cur]
        num_individuals = len(fitness)
        indices = list(range(len(fitness)))
        selected_indices = []
        selection_size = self.pop - 1

        while (len(selected_indices) < selection_size):
            np.random.shuffle(indices)
            idx_tournament = indices[0:self.tour_n]
            fit = []
            for i in range(len(idx_tournament)):
                fit.append(fitness[idx_tournament[i]])
            maxindex = fit.index(max(fit))
            winner = idx_tournament[maxindex]
            r = random.random()
            if r < self.p:
                selected_indices.append(winner)
            selected_indices = list(set(selected_indices))



        for i in range(len(selected_indices)):
            survive.append(x_cur[selected_indices[i]])

        return survive

    def cool(self):
        # fast:
        self.T = self.T_max * np.exp(-self.c * (self.cur_g * 10) ** self.quench)
        self.T_history.append(self.T)

    def isclose(self, a, b, rel_tol=1e-09, abs_tol=1e-30):
        return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    def disp(self):
        if self.shape == 1:
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)
            for i in range(len(self.x_history)):
                ax.cla()
                xmin, xmax = min(self.x_history[i]), max(self.x_history[i])
                x = np.arange(xmin, xmax, xmax/10000)
                y = np.zeros(shape=x.shape)
                for index in range(x.shape[0]):
                    y[index] = self.func(np.array([x[index]]))
                plt.plot(x, y,c='black')
                # 对每一代
                x, t = self.x_history[i], self.T_history[i]
                y = [self.func(xx) for xx in x]
                p = ax.scatter(x, y, marker='o',c='b')
                plt.title("当前温度 ：" + str(t) + '\n' + 'x_best:' + str(min(x)) + '\ny_best:' + str(self.func(min(x))))
                plt.pause(0.5)
                if i != len(self.x_history) - 1:
                    p.remove()
                else:
                    p = ax.scatter(self.x_best, self.y_best, c='r', marker='*',s=100)

            plt.show()

        elif self.shape == 2:
            fig = plt.figure()
            ax = plt.axes(projection='3d')
            x0_list = [[0 for col in range(len(self.x_history[0]))] for row in range(len(self.x_history))]
            x1_list = [[0 for col in range(len(self.x_history[0]))] for row in range(len(self.x_history))]
            for i in range(len(self.x_history)):
                for j in range(len(self.x_history[i])):
                    x0_list[i][j] = self.x_history[i][j][0]
                    x1_list[i][j] = self.x_history[i][j][1]

            for i in range(len(self.x_history)):
                ax.cla()
                x0 = [x[0] for x in self.x_history[i]]
                x1 = [x[1] for x in self.x_history[i]]
                x_min, x_max = min(x0), max(x0)
                y_min, y_max = min(x1), max(x1)
                x = np.arange(x_min, x_max, x_max/100)
                y = np.arange(y_min, y_max, x_max/100)
                X, Y = np.meshgrid(x, y)
                Z = self.func(np.array([X, Y]))
                ax.plot_surface(X, Y, Z, cmap='Blues', alpha=0.3)
                x0, x1, t = x0_list[i], x1_list[i], self.T_history[i]
                y = [self.func(x) for x in self.x_history[i]]
                plt.title("当前温度 ："+str(t)+'\n'+'x_best:'+str([x_min,y_min])+'\ny_best:'+str(self.func(np.array([x_min,y_min]))))
                p = ax.scatter(x0, x1, y, c='b')
                plt.pause(0.7)
                if i != len(self.x_history) - 1:
                    p.remove()
                else:
                    p = ax.scatter(self.x_best[0], self.x_best[1], self.y_best, c='r', marker='*',s=100)

            plt.xlabel("x0")
            plt.ylabel("x1")
            plt.show()
        else:
            pass

    def main(self):
        pop1 = self.init_pop()
        self.x_history.append(pop1)
        while self.T > self.T_min:
            print('----------------当前迭代代数是' + str(self.cur_g) + '-------------------')
            new_pop = self.generate(pop1)
            pop1 = self.tournament(new_pop)
            self.x_history.append(pop1)
            self.cool()
            print('当前温度'+str(self.T))
            self.cur_g = self.cur_g + 1
            sur_pop_y = [self.func(xx) for xx in pop1]
            if len(self.y_best_history) >= 2 and self.isclose(sur_pop_y[-1], sur_pop_y[-2]):
                best_index = sur_pop_y.index(min(sur_pop_y))
                self.x_best = pop1[best_index]
                self.y_best = sur_pop_y[best_index]
                self.y_best_history.append(self.y_best)
                break

            best_index = sur_pop_y.index(min(sur_pop_y))
            self.x_best = pop1[best_index]
            self.y_best = sur_pop_y[best_index]
            self.y_best_history.append(self.y_best)



if __name__ == "__main__":
    start = time.time()  # 开始计时
    #
    # x_min = np.array(-5)
    # x_max = np.array(5)
    # demo = GSA(func=fun2, T_max=1, T_min=1e-15, pop=50, new_pop=30, cur_g=1, p=0.9, tour_n=2, shape=1)
    #
    # x_min = np.array([-10,-10])
    # x_max = np.array([10,10])
    # demo = GSA(func=Rastrigrin, T_max=1, T_min=1e-20, pop=30, new_pop=30, cur_g=1, p=0.9, tour_n=2, shape=2)
    #
    x_min = np.array([-5, -5])
    x_max = np.array([5, 5])
    demo = GSA(func=Griewangk, T_max=1, T_min=1e-25, pop=30, new_pop=30, cur_g=1, p=0.9, tour_n=5, shape=2)

    #
    # x_min = np.array(-4)
    # x_max = np.array(4)
    # demo = GSA(func=fun1,T_max=1,T_min=1e-15,pop=50,new_pop=30,cur_g=1,p=0.9,tour_n=2,shape=1)

    demo.xrange(x_min, x_max)
    demo.main()
    demo.disp()
    end = time.time()  # 结束计时
    print("Duration time: %0.3f" % (end - start))  # 打印运行时间
    print('iterations:' + str(demo.cur_g))
    print('x_best:'+str(demo.x_best))
    print('y_best:'+str(demo.y_best))

