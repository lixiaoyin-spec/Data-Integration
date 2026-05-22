<?xml version="1.0" encoding="UTF-8"?>
<!-- 统一集成格式 → C(MySQL) 学生格式 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Students>
      <xsl:for-each select="Students/student">
        <student>
          <Sno><xsl:value-of select="id"/></Sno>
          <Snm><xsl:value-of select="name"/></Snm>
          <Sex><xsl:value-of select="sex"/></Sex>
          <Sde><xsl:value-of select="major"/></Sde>
          <Pwd><xsl:value-of select="id"/></Pwd>
        </student>
      </xsl:for-each>
    </Students>
  </xsl:template>

</xsl:stylesheet>
