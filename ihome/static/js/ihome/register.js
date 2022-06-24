// js读取cookie的方法
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 保存图片验证码编号
var imageCodeId = "";

function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

function generateImageCode() {
    // 形成图片验证码的后端地址， 设置到页面中，让浏览请求验证码图片
    // 1. 生成图片验证码编号
    imageCodeId = generateUUID();
    // 是指图片url
    var url = "/api/v1.0/image_codes/" + imageCodeId;
    $(".image-code img").attr("src",url);
}

function sendSMSCode() {
    // 点击 获取邮箱验证码 这个按钮后被执行的函数
    $(".emailcode-a").removeAttr("onclick");

    var email = $("#email").val();
    if (!email) {
        $("#email-err span").html("请填写正确的邮箱号！");
        $("#email-err").show();
        $(".emailcode-a").attr("onclick", "sendSMSCode();");
        return;
    } 
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写图片验证码！");
        $("#image-code-err").show();
        $(".emailcode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    // 构造向后端发送请求的参数
    var req_data = {
        image_code: imageCode, // 图片验证码的值
        image_code_id: imageCodeId, // 图片验证码的编号，（全局变量）
        email_s:email  //这里的email_s应与后端获取的和邮箱验证forms.py里的名称一致
    };
    // 向后端发送POST请求
    var jsonData = JSON.stringify(req_data);
    $.ajax({
        url:"/api/v1.0/sms_codes/",
        type:"post",
        data: jsonData,
        contentType: "application/json",
        dataType: "json",
        headers:{
            "X-CSRFToken":getCookie("csrf_token")
        },
         success: function (resp) {
            if (resp.errno == "0") {
                var num = 60;
                // 表示发送成功
                var timer = setInterval(function () {
                    if (num >= 1) {
                        // 修改倒计时文本
                        $(".emailcode-a").html(num + "秒");
                        num -= 1;
                } else {
                    $(".emailcode-a").html("获取邮箱验证码");
                    $(".emailcode-a").attr("onclick", "sendSMSCode();");
                    clearInterval(timer);
                }
            }, 1000, 60)
        }
        else {
            alert(resp.errmsg);
            $(".emailcode-a").attr("onclick", "sendSMSCode();");
            }
        }
    });

}

$(document).ready(function() {
    generateImageCode();
    $("#email").focus(function(){
        $("#email-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#emailcode").focus(function(){
        $("#email-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });


    // 为表单的提交补充自定义的函数行为 （提交事件e）
    $(".form-register").submit(function(e){
        // 阻止浏览器对于表单的默认自动提交行为
        e.preventDefault();

        var email = $("#email").val();
        var emailCode = $("#emailcode").val();
        var passwd = $("#password").val();
        var passwd2 = $("#password2").val();
        if (!email) {
            $("#emaile-err span").html("请填写正确的邮箱号！");
            $("#email-err").show();
            return;
        } 
        if (!emailCode) {
            $("#email-code-err span").html("请填写邮箱验证码！");
            $("#email-code-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        if (passwd != passwd2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }

        // 调用ajax向后端发送注册请求!!!
        var req_data = {
            email: email,
            sms_code: emailCode,
            password: passwd,
            password2: passwd2,
        };
        //使用stringify转换成json格式
        var req_json = JSON.stringify(req_data);
        $.ajax({
            url: "/api/v1.0/users/",
            type: "post",
            data: req_json,
            contentType: "application/json",
            dataType: "json",
            headers: {// 请求头，将csrf_token值放到请求头中，方便后端csrf进行验证
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 注册成功，跳转到主页
                    location.href = "/index.html";
                } else {
                    alert(resp.errmsg);
                }
            }
        })

    });
})