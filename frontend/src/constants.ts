export const STRUCTURE_COSTS: Record<string, number> = {
  'RC조': 2500000, // Reinforced Concrete
  '철골조': 2800000, // Steel
  '조적조': 1800000, // Masonry
  '목조': 2000000, // Wood
  '기타': 2000000,
};

export const USEFUL_LIFE: Record<string, number> = {
  'RC조': 40,
  '철골조': 40,
  '조적조': 25,
  '목조': 20,
  '기타': 30,
};

export const MOCK_BUILDINGS: Record<string, any> = {
  '서울시 강남구 테헤란로 123': {
    address: '서울시 강남구 테헤란로 123',
    structure: 'RC조',
    totalArea: 1500,
    approvalDate: '1995-05-20',
    age: 29,
    floors: 5,
  },
  '경기도 성남시 분당구 판교로 456': {
    address: '경기도 성남시 분당구 판교로 456',
    structure: '철골조',
    totalArea: 3200,
    approvalDate: '2010-11-12',
    age: 14,
    floors: 8,
  },
};
