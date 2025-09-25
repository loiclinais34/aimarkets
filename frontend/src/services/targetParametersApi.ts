import { apiService } from './api';

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
    const response = await apiService.get('/target-parameters/');
    return response.data;
  },

  async createTargetParameter(data: CreateTargetParameterRequest): Promise<TargetParameter> {
    const response = await apiService.post('/target-parameters/', data);
    return response.data;
  },

  async updateTargetParameter(id: number, data: UpdateTargetParameterRequest): Promise<TargetParameter> {
    const response = await apiService.put(`/target-parameters/${id}`, data);
    return response.data;
  },

  async deleteTargetParameter(id: number): Promise<void> {
    await apiService.delete(`/target-parameters/${id}`);
  },
};
