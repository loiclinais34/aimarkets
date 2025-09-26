import { apiClient } from './api';

export interface TargetParameter {
  id: number;
  symbol: string;
  parameter_name: string;
  parameter_value: number;
  created_at: string;
  updated_at: string;
}

export interface CreateTargetParameterRequest {
  symbol: string;
  parameter_name: string;
  parameter_value: number;
}

export interface UpdateTargetParameterRequest {
  symbol?: string;
  parameter_name?: string;
  parameter_value?: number;
}

export const targetParametersApi = {
  async getTargetParameters(): Promise<TargetParameter[]> {
    const response = await apiClient.get('/api/v1/target-parameters/');
    return response.data;
  },

  async createTargetParameter(data: CreateTargetParameterRequest): Promise<TargetParameter> {
    const response = await apiClient.post('/api/v1/target-parameters/', data);
    return response.data;
  },

  async updateTargetParameter(id: number, data: UpdateTargetParameterRequest): Promise<TargetParameter> {
    const response = await apiClient.put(`/api/v1/target-parameters/${id}`, data);
    return response.data;
  },

  async deleteTargetParameter(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/target-parameters/${id}`);
  },
};
