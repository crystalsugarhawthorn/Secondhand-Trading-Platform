from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Length, Regexp, NumberRange

# 用户注册表单
class RegisterForm(FlaskForm):
    学号 = StringField('学号', validators=[
        DataRequired(message='学号不能为空'),
        Length(min=6, max=20, message='学号长度必须为6-20位'),
        Regexp('^[0-9]+$', message='学号必须为数字')
    ])
    姓名 = StringField('姓名', validators=[DataRequired(message='姓名不能为空')])
    手机号 = StringField('手机号', validators=[
        DataRequired(message='手机号不能为空'),
        Regexp('^1[3-9][0-9]{9}$', message='请输入有效的11位手机号')
    ])
    密码 = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=6, message='密码至少6位')
    ])
    角色 = SelectField('角色', 
        choices=[('买家', '买家'), ('卖家', '卖家')],
        validators=[DataRequired(message='请选择角色')]
    )
    submit = SubmitField('注册')

# 用户登录表单
class LoginForm(FlaskForm):
    手机号 = StringField('手机号', validators=[DataRequired(message='手机号不能为空')])
    密码 = PasswordField('密码', validators=[DataRequired(message='密码不能为空')])
    角色 = SelectField('角色',
        choices=[('买家', '买家'), ('卖家', '卖家'), ('管理员', '管理员')],
        validators=[DataRequired(message='请选择角色')]
    )
    submit = SubmitField('登录')

# 商品发布表单
class SellForm(FlaskForm):
    名称 = StringField('商品名称', validators=[
        DataRequired(message='商品名称不能为空'),
        Length(max=100)
    ])
    描述 = TextAreaField('描述', validators=[Length(max=1000)])
    价格 = FloatField('价格', validators=[
        DataRequired(message='价格不能为空'),
        NumberRange(min=0, message='价格必须大于等于0')
    ])
    分类 = SelectField('分类', coerce=int, validators=[DataRequired(message='请选择分类')])
    submit = SubmitField('发布商品')

# 商品审核表单
class AdminReviewForm(FlaskForm):
    审核状态 = SelectField('审核状态',
        choices=[('待审核', '待审核'), ('已审核', '已审核'), ('未通过', '未通过')],
        validators=[DataRequired()]
    )
    submit = SubmitField('更新审核状态')

# 支付表单
class PayForm(FlaskForm):
    payment_method = SelectField('支付方式',
        choices=[('alipay', '支付宝'), ('wechat', '微信')],
        validators=[DataRequired()]
    )

# 评价表单
class ReviewForm(FlaskForm):
    评分 = SelectField('评分',
        choices=[(5, '5星'), (4, '4星'), (3, '3星'), (2, '2星'), (1, '1星')],
        validators=[DataRequired()]
    )
    评论文本 = TextAreaField('评价内容', validators=[Length(max=500)])
    submit = SubmitField('提交评价')