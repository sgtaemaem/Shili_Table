"""
视力计算模块 - 优化版本
根据距离和视力值计算E字母的像素大小
"""

class VisionCalculator:
    def __init__(self, screen_width=1024, screen_height=800):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 预计算常量，避免重复计算
        self.screen_width_mm = 340.0
        self.screen_height_mm = 270.0
        self.pixels_per_mm_x = screen_width / self.screen_width_mm
        self.pixels_per_mm_y = screen_height / self.screen_height_mm
        self.standard_distance_m = 5.0

        # 标准视力表：5米距离下E字边长（毫米）- 基于GB11533-2011标准
        self.standard_e_sizes_5m = {
            4.0: 72.7, 4.1: 57.7, 4.2: 45.8, 4.3: 36.4, 4.4: 28.9,
            4.5: 23.0, 4.6: 18.2, 4.7: 14.5, 4.8: 11.5, 4.9: 9.1,
            5.0: 7.27, 5.1: 5.8, 5.2: 4.6, 5.3: 3.6
        }

        # 预计算缩放因子，避免重复判断
        self.scale_factors = {
            4.0: 10.0, 4.1: 8.0, 4.2: 8.0, 4.3: 6.0, 4.4: 6.0,
            4.5: 6.0, 4.6: 4.0, 4.7: 4.0, 4.8: 4.0, 4.9: 3.0,
            5.0: 3.0, 5.1: 3.5, 5.2: 2.8, 5.3: 2.2
        }

        # 预计算视力序列，避免重复创建列表
        self.all_vision_levels = [5.3, 5.2, 5.1, 5.0, 4.9, 4.8, 4.7, 4.6, 4.5, 4.4, 4.3, 4.2, 4.1, 4.0]
        
    def calculate_e_size(self, vision_value, distance_cm):
        """
        优化版本：根据视力值和距离计算E字母的像素大小

        Args:
            vision_value: 视力值 (4.0-5.3)
            distance_cm: 测试距离(厘米)

        Returns:
            tuple: (width_pixels, height_pixels)
        """
        # 使用预计算的值，避免重复查找
        if vision_value not in self.standard_e_sizes_5m:
            vision_value = min(self.standard_e_sizes_5m.keys(),
                             key=lambda x: abs(x - vision_value))

        # 使用预计算的常量
        standard_size_5m_mm = self.standard_e_sizes_5m[vision_value]
        actual_size_mm = standard_size_5m_mm * (distance_cm * 0.01 / self.standard_distance_m)

        # 使用预计算的缩放因子
        scale_factor = self.scale_factors[vision_value]

        # 一次性计算像素大小
        width_pixels = max(min(int(actual_size_mm * self.pixels_per_mm_x * scale_factor), 250), 8)
        height_pixels = max(min(int(actual_size_mm * self.pixels_per_mm_y * scale_factor), 250), 8)

        return width_pixels, height_pixels
    
    def get_next_vision_level(self, current_vision, success=True, test_state=None):
        """
        优化版本：获取下一个视力测试级别
        """
        try:
            current_index = self.all_vision_levels.index(current_vision)
        except ValueError:
            return None

        if success:
            # 成功：向更高视力测试
            return self.all_vision_levels[current_index - 1] if current_index > 0 else None
        else:
            # 失败：根据失败次数决定下降幅度
            if test_state and test_state.get('total_failures', 0) > 2:
                # 超过2次失败：每次下降0.2
                new_vision = round(current_vision - 0.2, 1)
                return new_vision if new_vision >= 4.0 else 4.0
            else:
                # 前2次失败：每次下降0.1
                return (self.all_vision_levels[current_index + 1]
                       if current_index < len(self.all_vision_levels) - 1 else None)
    
    def is_test_complete(self, current_vision, consecutive_failures, test_results=None):
        """优化版本：判断测试是否完成"""
        return (current_vision == 4.0 or
                (current_vision == 5.3 and test_results and test_results[-1][1]))
    
    def calculate_final_vision(self, test_results):
        """优化版本：根据测试结果计算最终视力值"""
        if not test_results:
            return 5.0

        last_success_vision = None
        consecutive_failures = 0

        for vision_value, success in test_results:
            if success:
                last_success_vision = vision_value
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    return last_success_vision or 4.0

        # 测试正常结束
        last_vision, last_success = test_results[-1]
        return last_vision if last_success else (last_success_vision or 4.0)
