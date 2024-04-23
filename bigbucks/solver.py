import numpy as np
import pandas as pd

class Asset:
    def __init__(self, ticker, data):
        self.ticker = ticker
        self.data = data
        self.returns = (self.data.pct_change(fill_method=None))

    def get_rate(self):
        total_return = self.returns.sum().item()
        return total_return

    def get_dev(self):
        return self.returns.std()

    
class Solver():
    def compute(self, covariance_matrix, asset_vector, portfolio_return):
        self.r_p = portfolio_return
        self.covariance_matrix = covariance_matrix
        self.assets_vec = asset_vector
        self.compute_A()
        self.compute_b()
        self.compute_leftside()
        self.compute_rightside()
        self.compute_weights()
        self.compute_volatility()
        return self.volatility

    def compute_A(self):
        self.A = np.zeros((2, len(self.assets_vec)))
        for i in range(2):
            for j in range(len(self.assets_vec)):
                if i == 0:
                    self.A[i, j] = 1
                else:
                    self.A[i, j] = self.assets_vec[j].get_rate()
        self.A_T = self.A.transpose()

    def compute_b(self):
        self.b = np.array([1.0, self.r_p])

    def compute_leftside(self):
        rows = self.covariance_matrix.shape[0] + self.A.shape[0]
        cols = self.covariance_matrix.shape[1] + self.A_T.shape[1]
        self.leftside = np.zeros((rows, cols))
        for i in range(rows):
            for j in range(cols):
                if j < self.covariance_matrix.shape[1] and i < self.covariance_matrix.shape[0]:
                    self.leftside[i, j] = self.covariance_matrix.iloc[i, j]
                elif j >= self.covariance_matrix.shape[1] and i < self.covariance_matrix.shape[0]:
                    self.leftside[i, j] = self.A_T[i, j - self.covariance_matrix.shape[0]]
                elif j < self.covariance_matrix.shape[1] and i >= self.covariance_matrix.shape[0]:
                    self.leftside[i, j] = self.A[i - self.covariance_matrix.shape[0], j]
                else:
                    self.leftside[i, j] = 0.0

    def compute_rightside(self):
        rightside_rows = len(self.assets_vec) + 2
        self.rightside = np.zeros((rightside_rows, 1))
        for i in range(rightside_rows):
            if i < rightside_rows - 2:
                self.rightside[i, 0] = 0
            elif i == rightside_rows - 2:
                self.rightside[i, 0] = 1.0
            else:
                self.rightside[i, 0] = self.r_p

    def compute_weights(self):
        weights_temp = np.linalg.solve(self.leftside, self.rightside)
        self.weights = weights_temp[:self.covariance_matrix.shape[0]]
        return self.weights

    def compute_volatility(self):
        sum = 0
        for i in range(len(self.weights)):
            for j in range(len(self.weights)):
                sum += self.weights[i] * self.weights[j] * self.covariance_matrix.iloc[i, j]
        self.volatility = np.sqrt(sum)
        